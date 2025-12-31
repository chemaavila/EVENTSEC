from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status

from ..threatmap.aggregator import FilterState
from ..threatmap.runtime import get_runtime
from ..threatmap.schema import (
    ClientSetFilters,
    ClientTelemetry,
    IngestEventIn,
    WsAgg,
    WsEvent,
    WsHb,
    WsMode,
)

logger = logging.getLogger("eventsec.threatmap")

router = APIRouter(tags=["threatmap"])


@router.post("/ingest")
async def ingest(payload: Any) -> Dict[str, Any]:
    """Legal telemetry on-ramp.

    In live mode (default), the server emits ZERO events unless provided via /ingest
    (or other configured connectors not included here).
    """
    rt = get_runtime()
    if rt.cfg.telemetry_mode != "live":
        # still allow ingest, but keep semantics: ingested events are real
        pass

    items: list[IngestEventIn] = []
    try:
        if isinstance(payload, list):
            items = [IngestEventIn.model_validate(x) for x in payload]
        else:
            # Accept both already-parsed JSON (dict) and raw JSON strings.
            if isinstance(payload, (str, bytes, bytearray)):
                items = [IngestEventIn.model_validate_json(payload)]
            else:
                items = [IngestEventIn.model_validate(payload)]
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )

    accepted = 0
    for inp in items:
        evt = await rt.normalize_and_enrich(inp)
        await rt.dedupe_merge_or_publish(evt)
        accepted += 1

    return {"accepted": accepted}


def _filters_from_client(state: FilterState, msg: ClientSetFilters) -> FilterState:
    if msg.window:
        state.window = msg.window
    if msg.types is not None:
        state.types = set([str(t) for t in msg.types]) if msg.types else None
    if msg.min_severity is not None:
        state.min_severity = int(msg.min_severity)
    if msg.major_only is not None:
        state.major_only = bool(msg.major_only)
    if msg.country is not None:
        state.country = msg.country
    return state


@router.websocket("/ws/threatmap")
async def ws_threatmap(websocket: WebSocket) -> None:
    await websocket.accept()
    rt = get_runtime()

    # Per-connection state
    mode = "raw"
    mode_reason = "init"
    filters = FilterState(
        window="5m", types=None, min_severity=1, major_only=False, country=None
    )
    client_fps: float | None = None
    client_queue_len: int | None = None

    sub = await rt.bus.subscribe(max_queue=2000)

    async def send_json(obj: Any) -> None:
        await websocket.send_text(json.dumps(obj, default=str))

    # Initial replay + snapshot
    try:
        replay = rt.bus.replay()
        for pub in replay:
            await send_json(
                WsEvent(
                    server_ts=pub.server_ts, seq=pub.seq, payload=pub.event
                ).model_dump()
            )
        snap = rt.agg.snapshot(
            seq=(replay[-1].seq if replay else 0),
            window=filters.window,
            filters=filters,
        )
        await send_json(
            WsAgg(server_ts=snap.server_ts, seq=snap.seq, payload=snap).model_dump()
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Threatmap WS initial sync failed: %s", exc)

    async def hb_loop() -> None:
        while True:
            await asyncio.sleep(rt.cfg.hb_tick_ms / 1000.0)
            now = datetime.now(timezone.utc)
            await send_json(WsHb(server_ts=now, seq=rt.bus.next_seq()).model_dump())

    async def agg_loop() -> None:
        while True:
            await asyncio.sleep(rt.cfg.agg_tick_ms / 1000.0)
            snap = rt.agg.snapshot(
                seq=rt.bus.next_seq(), window=filters.window, filters=filters
            )
            await send_json(
                WsAgg(server_ts=snap.server_ts, seq=snap.seq, payload=snap).model_dump()
            )

    async def recv_loop() -> None:
        nonlocal mode, mode_reason, client_fps, client_queue_len
        while True:
            msg = await websocket.receive_text()
            try:
                obj = json.loads(msg)
            except Exception:
                continue

            t = obj.get("type")
            if t == "client_telemetry":
                telem = ClientTelemetry.model_validate(obj)
                client_fps = telem.render_fps
                client_queue_len = telem.queue_len
            elif t == "set_filters":
                fmsg = ClientSetFilters.model_validate(obj)
                _filters_from_client(filters, fmsg)

    async def pub_loop() -> None:
        nonlocal mode, mode_reason
        while True:
            pub = await sub.get()

            # Backpressure switching rules (real; never fabricate)
            # Inputs: server queue pressure (subscriber queue fill), client telemetry (fps/queue_len)
            qsize = sub.qsize()
            fps = client_fps or 60.0
            cql = client_queue_len or 0

            new_mode = mode
            new_reason = mode_reason
            if qsize > 1500 or cql > 800 or fps < 42:
                new_mode = "agg_only"
                new_reason = "backpressure"
            elif qsize > 600 or cql > 250 or fps < 55:
                new_mode = "hybrid"
                new_reason = "degraded"
            else:
                new_mode = "raw"
                new_reason = "healthy"

            if new_mode != mode:
                mode = new_mode
                mode_reason = new_reason
                now = datetime.now(timezone.utc)
                await send_json(
                    WsMode(server_ts=now, mode=mode, reason=mode_reason).model_dump()
                )

            # Sending policy by mode
            if mode == "agg_only":
                continue
            if mode == "hybrid" and not pub.event.is_major:
                # drop low severity first under load
                continue

            await send_json(
                WsEvent(
                    server_ts=pub.server_ts, seq=pub.seq, payload=pub.event
                ).model_dump()
            )

    hb_task = asyncio.create_task(hb_loop())
    agg_task = asyncio.create_task(agg_loop())
    recv_task = asyncio.create_task(recv_loop())
    pub_task = asyncio.create_task(pub_loop())

    try:
        await asyncio.gather(hb_task, agg_task, recv_task, pub_task)
    except WebSocketDisconnect:
        pass
    finally:
        hb_task.cancel()
        agg_task.cancel()
        recv_task.cancel()
        pub_task.cancel()
        await rt.bus.unsubscribe(sub)

#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


def _flatten(obj: Any, prefix: str = "") -> Dict[str, Any]:
    flattened: Dict[str, Any] = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else key
            flattened.update(_flatten(value, path))
    elif isinstance(obj, list):
        flattened[prefix] = obj
    else:
        flattened[prefix] = obj
    return flattened


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _infer_mapping(raw_rows: Iterable[Dict[str, Any]], norm_rows: Iterable[Dict[str, Any]]) -> List[Tuple[str, str]]:
    mappings: List[Tuple[str, str]] = []
    for raw, norm in zip(raw_rows, norm_rows):
        raw_flat = _flatten(raw)
        norm_flat = _flatten(norm)
        for norm_key, norm_val in norm_flat.items():
            for raw_key, raw_val in raw_flat.items():
                if norm_val == raw_val and norm_key not in [m[1] for m in mappings]:
                    mappings.append((raw_key, norm_key))
    return mappings


def main() -> int:
    raw_dir = Path("audit_inputs/events_raw")
    norm_dir = Path("audit_inputs/events_normalized")
    out_dir = Path("audit_inputs/docs")
    out_dir.mkdir(parents=True, exist_ok=True)

    for raw_path in raw_dir.glob("*.jsonl"):
        norm_path = norm_dir / raw_path.name
        if not norm_path.exists():
            raise SystemExit(f"Missing normalized sample for {raw_path.name}")
        raw_rows = _read_jsonl(raw_path)
        norm_rows = _read_jsonl(norm_path)
        if not raw_rows or not norm_rows:
            raise SystemExit(f"Empty samples for {raw_path.name}")
        mappings = _infer_mapping(raw_rows, norm_rows)
        source_name = raw_path.stem
        output = [
            f"# Mapping RAW → NORMALIZED ({source_name})",
            "",
            "| RAW.path | NORMALIZED.path |",
            "| --- | --- |",
        ]
        for raw_key, norm_key in mappings:
            output.append(f"| `{raw_key}` | `{norm_key}` |")
        output.append("")
        output.append("## Transformaciones detectadas")
        output.append("- NO DISPONIBLE: las transformaciones no se pueden inferir sin parser explícito.")
        (out_dir / f"mapping_{source_name}.md").write_text(
            "\n".join(output), encoding="utf-8"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

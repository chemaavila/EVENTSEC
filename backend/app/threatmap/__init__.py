"""Threat Map realtime telemetry pipeline (live-only by default).

This package provides:
- Canonical AttackEvent schema
- Deterministic GeoIP enrichment (MaxMind MMDB)
- In-memory event bus + replay buffer
- Server-authoritative aggregation + backpressure-aware streaming
"""

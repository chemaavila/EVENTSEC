# Threat Map (OpenSearch-backed)

## Fuente de datos
El Threat Map se alimenta de eventos reales indexados en OpenSearch (`network-events-*`).
No requiere POST manual para ver datos.

## Endpoint principal
`GET /threatmap/points`

Parámetros:
- `window` (ej: `5m`, `15m`, `1h`)
- `size` (máx 500)

Respuesta: lista de eventos con `src.geo` / `dst.geo` (lat/lon) y severidad.

## Telemetría mock (solo dev)
`THREATMAP_TELEMETRY_MODE=mock` habilita replay/telemetría simulada si se configura en el runtime.

## Nota de GeoIP
Configura `MAXMIND_DB_PATH` para enriquecer GeoIP de forma determinista.

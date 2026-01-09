# IDS (Suricata / Zeek) — comportamiento real por entorno

## Resumen
- **macOS + Docker Desktop**: los contenedores NO ven tráfico real del host por default. Usa eventos simulados o ejecuta el sensor en una VM Linux si necesitas captura real.
- **Linux**: habilita `network_mode: host` y selecciona la interfaz (`IDS_INTERFACE=eth0|any`) para capturar tráfico real del host.

## Dev en macOS (Docker Desktop)
Por diseño de Docker Desktop, el tráfico del host no entra en la red bridge del contenedor.
Esto implica que al visitar una URL en el navegador del host **no aparecerán** eventos IDS.

Recomendaciones:
- Usa el pipeline `/events` para inyectar eventos simulados.
- O ejecuta Suricata/Zeek en una VM Linux con acceso a la interfaz real.

## Linux (captura real)
Usa el override con `network_mode: host`:

```bash
docker compose --profile ids -f docker-compose.yml -f docker-compose.linux-ids.override.yml up -d
```

Opcional: selecciona interfaz
```bash
IDS_INTERFACE=any \
docker compose --profile ids -f docker-compose.yml -f docker-compose.linux-ids.override.yml up -d
```

## Notas
- El collector IDS (`ids_collector`) usa `EVENTSEC_API_BASE=http://127.0.0.1:8000` en modo host.
- Documenta cambios adicionales en `docs/DEPLOYMENT.md` si ajustas interfaces de captura.

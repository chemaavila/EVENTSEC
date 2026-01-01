# EDR Install (según repo)

Fuentes: `agent/README.md`, `agent/INSTALLATION_SUMMARY.md`, `agent/agent.py`.

## Plataformas soportadas (según doc)
- macOS (10.14+)
- Windows (10/11)
- Linux (Ubuntu, Debian, RHEL, etc.)

## Instalación / ejecución (resumen reproducible)
1) Construcción del ejecutable (scripts en `agent/`):
   - macOS: `build_macos.sh`
   - Windows: `build_windows.bat`
   - Linux: `build_linux.sh`
2) Configuración: editar `agent_config.json` (ejemplos en `agent/README.md`).
   - `api_url`, `agent_token`, `enrollment_key`, `log_paths`.
3) Enrollment: el agente llama `POST /agents/enroll` con `enrollment_key` (ver `agent/agent.py`).
4) Heartbeat: `POST /agents/{agent_id}/heartbeat` (ver `agent/agent.py`).

## Verificación
- Logs del agente (según doc): `agent.log` junto al binario.
- UI: pantalla de agentes/endpoints (según `agent/README.md`).

## NO DISPONIBLE
- Instaladores firmados, tokens reales y capturas de instalación no están en el repo.

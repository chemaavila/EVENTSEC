# EVENTSEC Agent Troubleshooting

## Agent not enrolling
- Confirm `enrollment_key` is correct and backend allows enrollment.
- Check outbound connectivity to `server_url`.

## Heartbeat missing
- Validate API key is set (config or state dir).
- Confirm `agents/{agent_id}/heartbeat` is reachable.

## Inventory not showing
- Ensure `inventory_interval` is set.
- Check spool depth: `eventsec-agent diagnose`.

## Logs
- Increase `log_level` to `debug`.
- For services, check system logs (systemd, Windows Event Log, macOS Console).

## Spool stuck
- Check disk usage and `max_spool_mb`.
- Verify backend is reachable and accepts inventory payloads.

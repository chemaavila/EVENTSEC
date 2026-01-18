# Software Technical Notes (SIEM + XDR/EDR)

> **Source note:** Software repositories could not be cloned in this environment due to network restrictions.
> These notes are based on the official Software architecture details provided in the task prompt and
> must be cross-checked against upstream repos once available.

## Architecture overview (official docs)
- Agent → Manager/Server (decoders + rules engine) → Alerts JSON → Filebeat → Indexer → Dashboard.
- Default ports: **1514/1515/55000/9200/443**.
- TLS is used between manager ↔ indexer and dashboard ↔ API.

## SIEM pipeline
- Decoders and rules are defined in `ruleset/` and transform raw logs into alerts.
- Alerts are indexed by Filebeat into `software-alerts-*` and `software-archives-*` indices.
- Alert fields include `rule.id`, `rule.level`, `rule.groups`, `agent.id`, `manager`, `timestamp`, `data.*`.

## XDR/EDR modules
- Key modules: FIM, vulnerability detection, configuration assessment, active response.
- Active response triggers by rule ID/level/groups and executes scripts on agents.

## API endpoints (official docs reference)
- `/agents`: list and manage agents.
- `/decoders`: list or fetch decoders.
- `/event`: ingest events.
- `/active-response`: trigger active response commands.
- Token-based auth (Bearer) with TLS.

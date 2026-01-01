#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def _load_schema(path: Path) -> Dict[str, Dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    tables = {}
    for table in data.get("tables", []):
        columns = {col["name"]: col.get("type") for col in table.get("columns", [])}
        tables[table["table_name"]] = columns
    return tables


def main() -> int:
    repo_schema_path = Path("audit_inputs/schemas/kql_schema.json")
    runtime_schema_path = Path("audit_inputs/schemas/kql_schema_runtime.json")
    output_path = Path("audit_inputs/schemas/schema_drift_report.md")

    if not repo_schema_path.exists() or not runtime_schema_path.exists():
        raise SystemExit("Missing schema files for drift report")

    repo_tables = _load_schema(repo_schema_path)
    runtime_tables = _load_schema(runtime_schema_path)

    repo_only = sorted(set(repo_tables) - set(runtime_tables))
    runtime_only = sorted(set(runtime_tables) - set(repo_tables))
    output_lines: List[str] = ["# Schema Drift Report", ""]

    output_lines.append("## Tables only in repo-derived schema")
    output_lines.append(", ".join(repo_only) if repo_only else "(none)")
    output_lines.append("")

    output_lines.append("## Tables only in runtime schema")
    output_lines.append(", ".join(runtime_only) if runtime_only else "(none)")
    output_lines.append("")

    output_lines.append("## Column differences")
    for table in sorted(set(repo_tables) & set(runtime_tables)):
        repo_cols = repo_tables[table]
        runtime_cols = runtime_tables[table]
        missing_cols = sorted(set(repo_cols) - set(runtime_cols))
        new_cols = sorted(set(runtime_cols) - set(repo_cols))
        type_changes = sorted(
            name
            for name in set(repo_cols) & set(runtime_cols)
            if repo_cols[name] != runtime_cols[name]
        )
        if not (missing_cols or new_cols or type_changes):
            continue
        output_lines.append(f"### {table}")
        if missing_cols:
            output_lines.append(f"- Missing in runtime: {', '.join(missing_cols)}")
        if new_cols:
            output_lines.append(f"- New in runtime: {', '.join(new_cols)}")
        if type_changes:
            output_lines.append(
                "- Type changes: "
                + ", ".join(
                    f"{name} ({repo_cols[name]} → {runtime_cols[name]})"
                    for name in type_changes
                )
            )
        output_lines.append("")

    output_path.write_text("\n".join(output_lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# PROTOXOL Endpoint Triage (Scanner)

This package runs a fast triage on an endpoint (Unix/macOS/Windows) gathering host info, process/network data, persistence artifacts, file inventory, optional YARA scans and optional VT/OTX reputation lookups.

## Installation

```bash
cd protoxol_triage_package
python3 -m venv .venv
source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows
pip install -r requirements.txt
# optional for YARA: pip install yara-python
```

## Execution

By default it scans auto-discovered paths:

```bash
python protoxol_triage.py --out triage_out --since-days 14 --max-files 4000
```

Add reputation lookups (requires `VT_API_KEY` & `OTX_API_KEY`) and zipped output:

```bash
python protoxol_triage.py --out triage_out --since-days 30 --max-files 4000 --zip --vt --otx
```

For YARA:

```bash
python protoxol_triage.py --out triage_out --since-days 30 --max-files 8000 --yara rules_sample.yar
```

## Output

Reports and CSVs are written under `triage_out/<host>_<timestamp>/`, plus `.zip` when requested.



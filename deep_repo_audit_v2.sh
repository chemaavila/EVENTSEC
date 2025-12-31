#!/usr/bin/env bash
set -Eeuo pipefail

TS="$(date +'%Y%m%d_%H%M%S')"
ROOT="$(pwd)"
OUT="$ROOT/.ci_forensic/$TS"
mkdir -p "$OUT"

REPORT="$OUT/REPORT.txt"
CODEMAP="$OUT/CODEMAP.txt"
ROUTES="$OUT/ROUTES_FASTAPI.txt"

# tee everything to report
exec > >(tee -a "$REPORT") 2>&1

section() {
  echo
  echo "=================================================================================================="
  echo "### $*"
  echo "=================================================================================================="
}

run_sh() {
  echo
  echo "---- CMD: $*"
  bash -lc "$*" || echo "!! EXIT=$? (non-fatal, continuing)"
}

section "RUN METADATA"
echo "DATE: $(date)"
echo "ROOT: $ROOT"
echo "OUT:  $OUT"
echo "REPORT: $REPORT"
echo "USER: $(whoami)"
echo "SHELL: $SHELL"
echo "VIRTUAL_ENV: ${VIRTUAL_ENV:-<none>}"
echo "PYTHON: $(python -V 2>&1)"
echo "PIP: $(python -m pip -V 2>&1)"
echo "PATH: $PATH"

section "SYSTEM SNAPSHOT"
run_sh "uname -a || true"
run_sh "sw_vers || true"
run_sh "id || true"
run_sh "ulimit -a || true"

section "GIT SNAPSHOT (if repo)"
run_sh "git rev-parse --is-inside-work-tree >/dev/null 2>&1 && git status -sb || true"
run_sh "git rev-parse --short HEAD 2>/dev/null || true"
run_sh "git log -n 20 --oneline --decorate 2>/dev/null || true"
run_sh "git diff --stat 2>/dev/null || true"

section "PYTHON TOOLCHAIN (MAX SIGNAL)"
run_sh "python -c 'import sys; print(sys.version); print(sys.executable); print(\"prefix=\", sys.prefix); print(\"base_prefix=\", sys.base_prefix)'"
run_sh "python -m pip check || true"
run_sh "python -m pip list || true"
run_sh "python -m pip freeze || true"

section "REPO TREE (CODE-ONLY) + (FULL BUT EXCLUDING GENERATED/CACHES)"
cat > "$OUT/tree_gen.py" <<'PY'
from __future__ import annotations
import os
from pathlib import Path

ROOT = Path(os.environ.get("ROOT", ".")).resolve()

# Exclude: venv, node_modules, caches, AND ANYTHING THAT STARTS WITH ".ci_"
EXCLUDE_DIRS = {
    ".git", ".venv", "node_modules", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "dist", "build", ".idea", ".vscode",
    ".ci_forensic", ".ci_local_full"
}
EXCLUDE_FILE_NAMES = {".DS_Store"}

def excluded(p: Path) -> bool:
    for part in p.parts:
        if part in EXCLUDE_DIRS:
            return True
        if part.startswith(".ci_"):   # critical fix
            return True
    if p.name in EXCLUDE_FILE_NAMES:
        return True
    return False

def human(n: int) -> str:
    units = ["B","KB","MB","GB","TB"]
    f = float(n)
    for u in units:
        if f < 1024.0:
            return f"{f:.1f}{u}" if u != "B" else f"{int(f)}B"
        f /= 1024.0
    return f"{f:.1f}PB"

def walk(root: Path, code_only: bool) -> list[str]:
    # If code_only, restrict to relevant folders + key configs
    allow_roots = {"backend", "agent", "frontend", ".github", "docker-compose.yml", "compose.yml", "pyproject.toml", "requirements.txt"}
    lines: list[str] = []

    def rec(p: Path, prefix: str = ""):
        try:
            entries = list(p.iterdir())
        except Exception as e:
            lines.append(prefix + f"[ERR] {p.name} ({e})")
            return

        # filter
        entries = [e for e in entries if not excluded(e)]
        dirs = sorted([e for e in entries if e.is_dir()], key=lambda x: x.name.lower())
        files = sorted([e for e in entries if e.is_file()], key=lambda x: x.name.lower())

        items = dirs + files
        for i, e in enumerate(items):
            last = (i == len(items)-1)
            branch = "└── " if last else "├── "
            next_prefix = prefix + ("    " if last else "│   ")
            if e.is_dir():
                lines.append(prefix + branch + e.name + "/")
                rec(e, next_prefix)
            else:
                try:
                    sz = e.stat().st_size
                    lines.append(prefix + branch + f"{e.name}  ({human(sz)})")
                except Exception:
                    lines.append(prefix + branch + f"{e.name}  (size: ?)")
    lines.append(str(root))

    if code_only:
        # show only allow_roots if present
        for name in sorted([x for x in allow_roots if (root / x).exists()]):
            p = root / name
            if p.is_dir():
                lines.append(f"└── {name}/")
                rec(p, "    ")
            else:
                try:
                    sz = p.stat().st_size
                    lines.append(f"└── {name}  ({human(sz)})")
                except Exception:
                    lines.append(f"└── {name}")
    else:
        rec(root, "")

    return lines

code_txt = "\n".join(walk(ROOT, True))
full_txt = "\n".join(walk(ROOT, False))

(Path(os.environ["OUT"]) / "PROJECT_TREE_CODE_ONLY.txt").write_text(code_txt + "\n", encoding="utf-8")
(Path(os.environ["OUT"]) / "PROJECT_TREE_FULL_EXCL.txt").write_text(full_txt + "\n", encoding="utf-8")
print("Saved PROJECT_TREE_CODE_ONLY.txt and PROJECT_TREE_FULL_EXCL.txt")
PY
ROOT="$ROOT" OUT="$OUT" python "$OUT/tree_gen.py"

section "STATIC DEEP CODEMAP (EVERY FILE -> symbols + calls) [EXCLUDING .ci_* + junk]"
cat > "$OUT/repo_introspect_v2.py" <<'PY'
from __future__ import annotations
import ast
import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("ROOT", ".")).resolve()
OUT = Path(os.environ.get("OUT", ".")).resolve()
FILES_DIR = OUT / "files"
FILES_DIR.mkdir(parents=True, exist_ok=True)

EXCLUDE_DIRS = {
    ".git", ".venv", "node_modules", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "dist", "build", ".idea", ".vscode",
    ".ci_forensic", ".ci_local_full"
}
EXCLUDE_FILE_NAMES = {".DS_Store"}

TEXT_SUFFIXES = {
    ".py",".md",".txt",".json",".yml",".yaml",".toml",".ini",".cfg",
    ".js",".ts",".tsx",".jsx",".css",".html",".sh",".zsh",".env",".example"
}

def excluded(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
        if part.startswith(".ci_"):  # critical fix
            return True
    if path.name in EXCLUDE_FILE_NAMES:
        return True
    return False

def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def safe_read_text(p: Path, max_bytes: int = 5_000_000) -> str:
    data = p.read_bytes()
    if len(data) > max_bytes:
        data = data[:max_bytes]
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("utf-8", errors="replace")

def doc_summary(s: str | None, maxlen: int = 260) -> str:
    if not s:
        return ""
    s = " ".join(s.strip().split())
    return s[:maxlen] + ("…" if len(s) > maxlen else "")

def node_to_str(n: ast.AST) -> str:
    try:
        return ast.unparse(n)
    except Exception:
        return n.__class__.__name__

def args_to_signature(a: ast.arguments) -> str:
    def fmt_arg(arg: ast.arg) -> str:
        s = arg.arg
        if arg.annotation:
            s += f": {node_to_str(arg.annotation)}"
        return s
    parts: list[str] = []
    posonly = [fmt_arg(x) for x in getattr(a, "posonlyargs", [])]
    if posonly:
        parts += posonly
        parts.append("/")
    parts += [fmt_arg(x) for x in a.args]
    if a.vararg:
        parts.append("*" + fmt_arg(a.vararg))
    if a.kwonlyargs:
        if not a.vararg:
            parts.append("*")
        parts += [fmt_arg(x) for x in a.kwonlyargs]
    if a.kwarg:
        parts.append("**" + fmt_arg(a.kwarg))
    return "(" + ", ".join(parts) + ")"

def get_returns(n: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    if n.returns:
        return " -> " + node_to_str(n.returns)
    return ""

def collect_calls(node: ast.AST) -> list[str]:
    calls: list[str] = []
    class V(ast.NodeVisitor):
        def visit_Call(self, n: ast.Call) -> Any:
            fn = n.func
            if isinstance(fn, ast.Name):
                calls.append(fn.id)
            elif isinstance(fn, ast.Attribute):
                chain = []
                cur: ast.AST = fn
                while isinstance(cur, ast.Attribute):
                    chain.append(cur.attr)
                    cur = cur.value
                if isinstance(cur, ast.Name):
                    chain.append(cur.id)
                calls.append(".".join(reversed(chain)))
            else:
                calls.append(fn.__class__.__name__)
            self.generic_visit(n)
    V().visit(node)
    return calls

def tally(calls: list[str]) -> dict[str,int]:
    m: dict[str,int] = {}
    for c in calls:
        m[c]=m.get(c,0)+1
    return dict(sorted(m.items(), key=lambda kv:(-kv[1], kv[0])))

def guess_purpose(path: Path, text: str) -> str:
    rp = rel(path).replace("\\","/")
    low = text.lower()
    hints: list[str] = []
    if "/routers/" in rp:
        hints.append("API router (FastAPI routes)")
    if rp.endswith("main.py") and "fastapi" in low:
        hints.append("FastAPI app entrypoint")
    if rp.endswith("models.py") and ("sqlalchemy" in low or "mapped_column" in low):
        hints.append("SQLAlchemy models")
    if "schemas" in rp and "pydantic" in low:
        hints.append("Pydantic schemas/validation")
    if "threatmap" in rp:
        hints.append("ThreatMap pipeline component")
    if rp.startswith("agent/"):
        hints.append("Endpoint agent component")
    if "websocket" in low:
        hints.append("WebSocket-related")
    if "opensearch" in low:
        hints.append("OpenSearch integration")
    if "prometheus" in low:
        hints.append("Prometheus/metrics")
    if not hints:
        return "General module / utilities"
    seen=set(); out=[]
    for h in hints:
        if h not in seen:
            out.append(h); seen.add(h)
    return "; ".join(out)

@dataclass
class PySymbol:
    kind: str
    name: str
    signature: str = ""
    returns: str = ""
    decorators: list[str] | None = None
    doc: str = ""
    bases: list[str] | None = None
    methods: list["PySymbol"] | None = None
    calls: dict[str,int] | None = None

def parse_python(text: str) -> dict[str, Any]:
    t = ast.parse(text)
    module_doc = ast.get_docstring(t)
    imports: list[str] = []
    globals_: list[str] = []
    symbols: list[PySymbol] = []
    module_calls: dict[str,int] = {}

    for node in t.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(node_to_str(node))
        elif isinstance(node, ast.Assign):
            for trg in node.targets:
                if isinstance(trg, ast.Name):
                    globals_.append(trg.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            decos=[node_to_str(d) for d in node.decorator_list] if node.decorator_list else []
            sig=args_to_signature(node.args)
            ret=get_returns(node)
            doc=doc_summary(ast.get_docstring(node))
            calls=tally(collect_calls(node))
            for k,v in calls.items():
                module_calls[k]=module_calls.get(k,0)+v
            symbols.append(PySymbol(
                kind="async_function" if isinstance(node, ast.AsyncFunctionDef) else "function",
                name=node.name,
                signature=sig,
                returns=ret,
                decorators=decos or None,
                doc=doc,
                calls=calls or None
            ))
        elif isinstance(node, ast.ClassDef):
            bases=[node_to_str(b) for b in node.bases] if node.bases else []
            decos=[node_to_str(d) for d in node.decorator_list] if node.decorator_list else []
            cdoc=doc_summary(ast.get_docstring(node))
            methods: list[PySymbol] = []
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    mdecos=[node_to_str(d) for d in sub.decorator_list] if sub.decorator_list else []
                    msig=args_to_signature(sub.args)
                    mret=get_returns(sub)
                    mdoc=doc_summary(ast.get_docstring(sub))
                    mcalls=tally(collect_calls(sub))
                    for k,v in mcalls.items():
                        module_calls[k]=module_calls.get(k,0)+v
                    methods.append(PySymbol(
                        kind="async_method" if isinstance(sub, ast.AsyncFunctionDef) else "method",
                        name=sub.name,
                        signature=msig,
                        returns=mret,
                        decorators=mdecos or None,
                        doc=mdoc,
                        calls=mcalls or None
                    ))
            symbols.append(PySymbol(
                kind="class",
                name=node.name,
                decorators=decos or None,
                doc=cdoc,
                bases=bases or None,
                methods=methods or None
            ))
    return {
        "module_doc": doc_summary(module_doc, 420),
        "imports": imports,
        "globals": sorted(set(globals_)),
        "symbols": symbols,
        "module_calls": dict(sorted(module_calls.items(), key=lambda kv:(-kv[1], kv[0]))),
    }

def parse_js_ts_symbols(text: str) -> dict[str, Any]:
    # best-effort scan for function/class/const arrow declarations
    funcs=set()
    classes=set()
    exports=set()

    for m in re.finditer(r"\bexport\s+(?:default\s+)?(?:function|const|class|interface|type)\s+([A-Za-z0-9_]+)", text):
        exports.add(m.group(1))

    for m in re.finditer(r"\bfunction\s+([A-Za-z0-9_]+)\s*\(", text):
        funcs.add(m.group(1))

    for m in re.finditer(r"\bconst\s+([A-Za-z0-9_]+)\s*=\s*\(", text):
        funcs.add(m.group(1))

    for m in re.finditer(r"\bconst\s+([A-Za-z0-9_]+)\s*=\s*async\s*\(", text):
        funcs.add(m.group(1))

    for m in re.finditer(r"\bclass\s+([A-Za-z0-9_]+)\b", text):
        classes.add(m.group(1))

    return {
        "exports": sorted(exports),
        "functions": sorted(funcs),
        "classes": sorted(classes),
    }

def build_import_graph(py_files: list[Path]) -> dict[str, set[str]]:
    graph: dict[str,set[str]] = {}
    for p in py_files:
        txt = safe_read_text(p)
        try:
            t = ast.parse(txt)
        except Exception:
            continue
        src = rel(p).replace("/", ".").replace("\\",".")
        src = re.sub(r"\.py$", "", src)
        deps=set()
        for n in ast.walk(t):
            if isinstance(n, ast.Import):
                for a in n.names:
                    deps.add(a.name)
            elif isinstance(n, ast.ImportFrom):
                if n.module:
                    deps.add(n.module)
        graph[src]=deps
    return graph

def main():
    all_files=[]
    py_files=[]
    for p in ROOT.rglob("*"):
        if excluded(p):
            continue
        if p.is_file():
            all_files.append(p)
            if p.suffix==".py":
                py_files.append(p)

    all_files=sorted(all_files, key=lambda x: rel(x).lower())
    py_files=sorted(py_files, key=lambda x: rel(x).lower())

    index={"root": str(ROOT), "counts": {"files_total": len(all_files), "py_files": len(py_files)}, "files":[]}

    codemap_lines=[]
    codemap_lines.append(f"ROOT: {ROOT}")
    codemap_lines.append(f"FILES_TOTAL (excluded junk/.ci_*): {len(all_files)}")
    codemap_lines.append(f"PY_FILES: {len(py_files)}")
    codemap_lines.append("")

    for p in all_files:
        rp=rel(p)
        info={"path": rp, "suffix": p.suffix}
        try:
            st=p.stat()
            info["size"]=st.st_size
        except Exception:
            info["size"]=None
        info["sha256"]=sha256(p) if info["size"] is not None else None

        if p.name in EXCLUDE_FILE_NAMES:
            continue

        if p.suffix in TEXT_SUFFIXES:
            txt=safe_read_text(p)
            info["lines"]=txt.count("\n")+1
            info["purpose_guess"]=guess_purpose(p, txt)

            per=[]
            per.append(f"FILE: {rp}")
            per.append(f"SIZE: {info['size']} bytes")
            per.append(f"LINES: {info['lines']}")
            per.append(f"SHA256: {info['sha256']}")
            per.append(f"PURPOSE: {info['purpose_guess']}")
            per.append("")

            if p.suffix==".py":
                try:
                    sym=parse_python(txt)
                    per.append("MODULE DOC (summary):")
                    per.append(sym["module_doc"] or "<none>")
                    per.append("")
                    per.append("IMPORTS:")
                    per.extend([f"  - {x}" for x in sym["imports"]] or ["  <none>"])
                    per.append("")
                    per.append("GLOBALS:")
                    per.extend([f"  - {x}" for x in sym["globals"]] or ["  <none>"])
                    per.append("")
                    per.append("SYMBOLS:")
                    for s in sym["symbols"]:
                        if s.kind=="class":
                            per.append(f"  [CLASS] {s.name}" + (f" bases={s.bases}" if s.bases else ""))
                            if s.decorators: per.append(f"    decorators: {s.decorators}")
                            if s.doc: per.append(f"    doc: {s.doc}")
                            if s.methods:
                                for m in s.methods:
                                    per.append(f"    [METHOD] {m.name}{m.signature}{m.returns}")
                                    if m.decorators: per.append(f"      decorators: {m.decorators}")
                                    if m.doc: per.append(f"      doc: {m.doc}")
                                    if m.calls:
                                        per.append("      calls (top):")
                                        for k,v in list(m.calls.items())[:80]:
                                            per.append(f"        - {k} (x{v})")
                        else:
                            per.append(f"  [FUNC] {s.name}{s.signature}{s.returns}")
                            if s.decorators: per.append(f"    decorators: {s.decorators}")
                            if s.doc: per.append(f"    doc: {s.doc}")
                            if s.calls:
                                per.append("    calls (top):")
                                for k,v in list(s.calls.items())[:80]:
                                    per.append(f"      - {k} (x{v})")
                    per.append("")
                    per.append("MODULE CALL HEATMAP (top):")
                    if sym["module_calls"]:
                        for k,v in list(sym["module_calls"].items())[:120]:
                            per.append(f"  - {k} (x{v})")
                    else:
                        per.append("  <none>")
                    per.append("")

                    sym_json = FILES_DIR / (rp.replace("/", "__") + ".symbols.json")
                    sym_json.write_text(json.dumps({
                        "path": rp,
                        "module_doc": sym["module_doc"],
                        "imports": sym["imports"],
                        "globals": sym["globals"],
                        "symbols": [s.__dict__ for s in sym["symbols"]],
                        "module_calls": sym["module_calls"]
                    }, indent=2), encoding="utf-8")
                    info["symbols_json"]=str(sym_json.relative_to(OUT))

                except Exception as e:
                    per.append(f"[PY PARSE ERROR] {e}")

            elif p.suffix in {".ts",".tsx",".js",".jsx"}:
                js=parse_js_ts_symbols(txt)
                per.append("JS/TS SYMBOL SCAN (best-effort):")
                per.append(f"  exports: {len(js['exports'])}")
                per.append(f"  functions: {len(js['functions'])}")
                per.append(f"  classes: {len(js['classes'])}")
                if js["exports"]:
                    per.append("  export names:")
                    per.extend([f"    - {x}" for x in js["exports"][:120]])
                if js["functions"]:
                    per.append("  function-like names:")
                    per.extend([f"    - {x}" for x in js["functions"][:200]])
                if js["classes"]:
                    per.append("  class names:")
                    per.extend([f"    - {x}" for x in js["classes"][:120]])
                per.append("")

            out_txt = FILES_DIR / (rp.replace("/", "__") + ".txt")
            out_txt.write_text("\n".join(per) + "\n", encoding="utf-8")
            info["analysis_txt"]=str(out_txt.relative_to(OUT))

            # Also append to CODEMAP (full consolidated)
            codemap_lines.append("\n".join(per))
            codemap_lines.append("\n" + ("-"*96) + "\n")

        index["files"].append(info)

    # Import graph
    graph = build_import_graph(py_files)
    (OUT / "IMPORT_GRAPH.json").write_text(json.dumps({k: sorted(list(v)) for k,v in graph.items()}, indent=2), encoding="utf-8")

    # Write index + codemap
    (OUT / "INDEX.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    (OUT / "CODEMAP.txt").write_text("\n".join(codemap_lines) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
PY

ROOT="$ROOT" OUT="$OUT" python "$OUT/repo_introspect_v2.py"
echo "Saved: $OUT/CODEMAP.txt"
echo "Saved: $OUT/INDEX.json"
echo "Saved per-file: $OUT/files/"
echo "Saved: $OUT/IMPORT_GRAPH.json"

section "RUNTIME: TRY TO DUMP FASTAPI ROUTES (SAFE MODE)"
cat > "$OUT/dump_routes.py" <<'PY'
from __future__ import annotations
import os
import sys
from pprint import pprint

# reduce side-effects during import if your app reads env
os.environ.setdefault("EVENTSEC_ENV", "audit")
os.environ.setdefault("PYTHONUNBUFFERED", "1")
ROOT = os.environ.get("ROOT")
if ROOT and ROOT not in sys.path:
    sys.path.insert(0, ROOT)

def main():
    try:
        from backend.app.main import app
    except Exception as e:
        print("[FAIL] Could not import backend.app.main:app")
        print("Error:", repr(e))
        return 1

    print("[OK] Imported FastAPI app:", app)
    routes = getattr(app, "routes", [])
    print("ROUTES_COUNT:", len(routes))
    print("")
    for r in routes:
        # starlette routes have .path and .methods sometimes
        path = getattr(r, "path", None)
        name = getattr(r, "name", None)
        methods = getattr(r, "methods", None)
        endpoint = getattr(r, "endpoint", None)
        print(f"- path={path} methods={sorted(methods) if methods else methods} name={name} endpoint={endpoint}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
PY

# dump to file but also show in report
python "$OUT/dump_routes.py" | tee "$ROUTES" || true
echo "Saved: $ROUTES"

section "STATIC CHECKS (RUFF / BANDIT / COMPILEALL)"
run_sh "python -m compileall -q backend agent || true"

run_sh "ruff --version || true"
run_sh "ruff check backend agent || true"
run_sh "ruff format --check backend agent || true"

run_sh "bandit --version || true"
run_sh "bandit -r backend agent -f txt -o '$OUT/BANDIT.txt' || true"
echo "Saved: $OUT/BANDIT.txt"

section "TESTS (PYTEST BACKEND + AGENT) + COVERAGE"
run_sh "pytest --version || true"
run_sh "PYTHONPATH='$ROOT' pytest -ra -vv backend/tests | tee '$OUT/pytest.backend.txt' || true"
run_sh "PYTHONPATH='$ROOT' pytest -ra -vv agent/tests   | tee '$OUT/pytest.agent.txt'   || true"
echo "Saved: $OUT/pytest.backend.txt"
echo "Saved: $OUT/pytest.agent.txt"

run_sh "python -m coverage --version || true"
run_sh "PYTHONPATH='$ROOT' python -m coverage run -m pytest -q backend/tests agent/tests || true"
run_sh "python -m coverage report -m | tee '$OUT/coverage.txt' || true"
run_sh "python -m coverage xml -o '$OUT/coverage.xml' || true"
echo "Saved: $OUT/coverage.txt"
echo "Saved: $OUT/coverage.xml"

section "QUICK POINTERS (WHERE TO LOOK)"
echo "MASTER REPORT: $REPORT"
echo "CODEMAP (all files merged): $CODEMAP"
echo "FASTAPI ROUTES: $ROUTES"
echo "TREES:"
echo " - $OUT/PROJECT_TREE_CODE_ONLY.txt"
echo " - $OUT/PROJECT_TREE_FULL_EXCL.txt"
echo "PER-FILE ANALYSIS FOLDER: $OUT/files/"
echo "IMPORT GRAPH JSON: $OUT/IMPORT_GRAPH.json"
echo "INDEX JSON: $OUT/INDEX.json"

section "DONE"

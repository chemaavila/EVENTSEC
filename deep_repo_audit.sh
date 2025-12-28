#!/usr/bin/env bash
set -Eeuo pipefail

TS="$(date +'%Y%m%d_%H%M%S')"
ROOT="$(pwd)"
OUT="$ROOT/.ci_forensic/$TS"
FILES_DIR="$OUT/files"
mkdir -p "$OUT" "$FILES_DIR"

REPORT="$OUT/REPORT.txt"
touch "$REPORT"

# everything into one report + console
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

section "HIGH-SIGNAL SYSTEM SNAPSHOT"
run_sh "uname -a || true"
run_sh "sw_vers || true"
run_sh "id || true"
run_sh "ulimit -a || true"

section "PROJECT TREE (FULL, INCLUDING FILE SIZES)"
# We'll generate a deterministic tree via Python (no reliance on `tree` command).
cat > "$OUT/tree_gen.py" <<'PY'
from __future__ import annotations
import os
from pathlib import Path

ROOT = Path(os.environ.get("ROOT", ".")).resolve()

EXCLUDE_DIRS = {
    ".git", ".venv", "node_modules", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".ci_forensic", "dist", "build", ".idea", ".vscode"
}

def human(n: int) -> str:
    units = ["B","KB","MB","GB","TB"]
    f = float(n)
    for u in units:
        if f < 1024.0:
            return f"{f:.1f}{u}" if u != "B" else f"{int(f)}B"
        f /= 1024.0
    return f"{f:.1f}PB"

def walk_tree(root: Path) -> list[str]:
    lines: list[str] = []
    def rec(p: Path, prefix: str = ""):
        try:
            entries = list(p.iterdir())
        except Exception as e:
            lines.append(prefix + f"[ERR] {p.name} ({e})")
            return
        dirs = sorted([e for e in entries if e.is_dir()], key=lambda x: x.name.lower())
        files = sorted([e for e in entries if e.is_file()], key=lambda x: x.name.lower())

        # filter dirs
        dirs = [d for d in dirs if d.name not in EXCLUDE_DIRS]

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
    rec(root, "")
    return lines

print("\n".join(walk_tree(ROOT)))
PY

ROOT="$ROOT" python "$OUT/tree_gen.py" | tee "$OUT/PROJECT_TREE.txt" >/dev/null
echo "Saved: $OUT/PROJECT_TREE.txt"

section "DEEP STATIC CODE DOCUMENTATION (EVERY FILE -> purpose + symbol tree + calls)"
cat > "$OUT/repo_introspect.py" <<'PY'
from __future__ import annotations
import ast
import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(os.environ.get("ROOT", ".")).resolve()
OUT = Path(os.environ.get("OUT", ".")).resolve()
FILES_DIR = OUT / "files"
FILES_DIR.mkdir(parents=True, exist_ok=True)

EXCLUDE_DIRS = {
    ".git", ".venv", "node_modules", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".ci_forensic", "dist", "build", ".idea", ".vscode"
}

TEXT_SUFFIXES = {
    ".py",".md",".txt",".json",".yml",".yaml",".toml",".ini",".cfg",
    ".js",".ts",".tsx",".jsx",".css",".html",".sh",".zsh",".env",".example"
}

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def safe_read_text(p: Path, max_bytes: int = 5_000_000) -> str:
    # limit to prevent huge files from exploding memory
    data = p.read_bytes()
    if len(data) > max_bytes:
        data = data[:max_bytes]
    # try utf-8 then fallback
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("utf-8", errors="replace")

def is_excluded(path: Path) -> bool:
    parts = set(path.parts)
    return any(d in parts for d in EXCLUDE_DIRS)

def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))

def normalize_out_path_for_file(p: Path) -> Path:
    # write per-file analysis to a stable filename
    # replace path separators to avoid nesting too deep
    safe = rel(p).replace("/", "__")
    return FILES_DIR / f"{safe}.txt"

def doc_summary(s: str | None, maxlen: int = 240) -> str:
    if not s:
        return ""
    s = " ".join(s.strip().split())
    return s[:maxlen] + ("…" if len(s) > maxlen else "")

def node_to_str(n: ast.AST) -> str:
    # best-effort conversion for decorators / annotations / bases
    try:
        return ast.unparse(n)  # py>=3.9
    except Exception:
        return n.__class__.__name__

def args_to_signature(a: ast.arguments) -> str:
    def fmt_arg(arg: ast.arg) -> str:
        s = arg.arg
        if arg.annotation:
            s += f": {node_to_str(arg.annotation)}"
        return s

    parts: list[str] = []

    # posonly
    posonly = [fmt_arg(x) for x in getattr(a, "posonlyargs", [])]
    if posonly:
        parts += posonly
        parts.append("/")

    # normal args
    parts += [fmt_arg(x) for x in a.args]

    # vararg
    if a.vararg:
        parts.append("*" + fmt_arg(a.vararg))

    # kwonly
    if a.kwonlyargs:
        if not a.vararg:
            parts.append("*")
        parts += [fmt_arg(x) for x in a.kwonlyargs]

    # kwarg
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
                # build attr chain: a.b.c
                chain = []
                cur: ast.AST = fn
                while isinstance(cur, ast.Attribute):
                    chain.append(cur.attr)
                    cur = cur.value
                if isinstance(cur, ast.Name):
                    chain.append(cur.id)
                chain = list(reversed(chain))
                calls.append(".".join(chain))
            else:
                calls.append(fn.__class__.__name__)
            self.generic_visit(n)
    V().visit(node)
    # keep deterministic order but don't lose multiplicity completely
    # we’ll provide unique + top frequency-ish info
    return calls

def guess_purpose(path: Path, text: str) -> str:
    rp = rel(path)
    low = text.lower()
    hints: list[str] = []

    # path-based roles
    if "/routers/" in rp.replace("\\", "/"):
        hints.append("API router (FastAPI route collection)")
    if rp.endswith("main.py") and "fastapi" in low:
        hints.append("FastAPI application entrypoint (app instance + routes)")
    if rp.endswith("models.py") and ("sqlalchemy" in low or "mapped_column" in low):
        hints.append("Database models.ops mapping (SQLAlchemy)")
    if "schemas" in rp and "pydantic" in low:
        hints.append("Data schemas / validation models (Pydantic)")
    if "threatmap" in rp:
        hints.append("ThreatMap pipeline component (telemetry/aggregation/runtime)")
    if "agent" in rp.replace("\\", "/").split("/"):
        hints.append("Endpoint agent component (local service / heartbeat / config)")

    # import-based heuristics
    if "from fastapi" in low or "import fastapi" in low:
        hints.append("Uses FastAPI")
    if "sqlalchemy" in low:
        hints.append("Uses SQLAlchemy")
    if "websocket" in low:
        hints.append("WebSocket-related")
    if "requests" in low:
        hints.append("HTTP client (requests)")
    if "opensearch" in low:
        hints.append("OpenSearch integration")
    if "prometheus" in low:
        hints.append("Metrics/Prometheus instrumentation")
    if "alembic" in low:
        hints.append("Migrations/Alembic")

    if not hints:
        return "General module / utilities (no strong heuristic match)"
    # dedupe while preserving order
    seen=set()
    out=[]
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
    calls: dict[str, int] | None = None

def parse_python_symbols(text: str) -> dict[str, Any]:
    tree = ast.parse(text)
    module_doc = ast.get_docstring(tree)

    imports: list[str] = []
    globals_: list[str] = []
    symbols: list[PySymbol] = []
    local_module_calls: dict[str,int] = {}

    def tally_calls(call_list: list[str]) -> dict[str,int]:
        m: dict[str,int] = {}
        for c in call_list:
            m[c]=m.get(c,0)+1
        return dict(sorted(m.items(), key=lambda kv:(-kv[1], kv[0])))

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(node_to_str(node))
        elif isinstance(node, ast.Assign):
            # global constants/vars (best-effort)
            targets=[]
            for t in node.targets:
                if isinstance(t, ast.Name):
                    targets.append(t.id)
                else:
                    targets.append(node_to_str(t))
            globals_.extend(targets)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            decos=[node_to_str(d) for d in node.decorator_list] if node.decorator_list else []
            sig=args_to_signature(node.args)
            ret=get_returns(node)
            doc=doc_summary(ast.get_docstring(node))
            calls=tally_calls(collect_calls(node))
            # accumulate module-level call counts too
            for k,v in calls.items():
                local_module_calls[k]=local_module_calls.get(k,0)+v
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
                    mcalls=tally_calls(collect_calls(sub))
                    for k,v in mcalls.items():
                        local_module_calls[k]=local_module_calls.get(k,0)+v
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
        "module_doc": doc_summary(module_doc, 400),
        "imports": imports,
        "globals": sorted(set(globals_)),
        "symbols": symbols,
        "module_calls": dict(sorted(local_module_calls.items(), key=lambda kv:(-kv[1], kv[0]))),
    }

def parse_ts_exports(text: str) -> dict[str, Any]:
    # lightweight export extraction (not a TS parser)
    exports = []
    for m in re.finditer(r"export\s+(?:default\s+)?(?:function|const|class|interface|type)\s+([A-Za-z0-9_]+)", text):
        exports.append(m.group(1))
    return {"exports": sorted(set(exports))}

def build_import_graph(py_files: list[Path]) -> dict[str, set[str]]:
    graph: dict[str,set[str]] = {}
    for p in py_files:
        txt = safe_read_text(p)
        try:
            t = ast.parse(txt)
        except Exception:
            continue
        src_mod = rel(p).replace("/", ".").replace("\\", ".")
        src_mod = re.sub(r"\.py$", "", src_mod)
        deps: set[str] = set()
        for n in ast.walk(t):
            if isinstance(n, ast.Import):
                for a in n.names:
                    deps.add(a.name)
            elif isinstance(n, ast.ImportFrom):
                if n.module:
                    deps.add(n.module)
        graph[src_mod] = deps
    return graph

def to_dot(graph: dict[str, set[str]], only_internal_prefixes: tuple[str,...]) -> str:
    # keep only edges that mention our repo modules
    # approximate internal modules by prefixes
    lines = ["digraph imports {", "  rankdir=LR;"]
    for s, deps in graph.items():
        for d in deps:
            if s.startswith(only_internal_prefixes) and d.startswith(only_internal_prefixes):
                lines.append(f'  "{s}" -> "{d}";')
    lines.append("}")
    return "\n".join(lines)

def main():
    all_files: list[Path] = []
    py_files: list[Path] = []

    for p in ROOT.rglob("*"):
        if is_excluded(p):
            continue
        if p.is_file():
            all_files.append(p)
            if p.suffix == ".py":
                py_files.append(p)

    all_files_sorted = sorted(all_files, key=lambda x: rel(x).lower())

    # master indexes
    index = {
        "root": str(ROOT),
        "counts": {
            "files_total": len(all_files_sorted),
            "py_files": len(py_files),
        },
        "files": [],
    }

    # per-file analysis
    for p in all_files_sorted:
        rp = rel(p)
        info: dict[str, Any] = {"path": rp}
        try:
            st = p.stat()
            info["size"] = st.st_size
        except Exception:
            info["size"] = None

        info["sha256"] = sha256(p) if info["size"] is not None else None
        info["suffix"] = p.suffix

        # only analyze known text-ish files
        if p.suffix in TEXT_SUFFIXES:
            txt = safe_read_text(p)
            info["lines"] = txt.count("\n") + 1

            # purpose guess
            info["purpose_guess"] = guess_purpose(p, txt)

            analysis_lines: list[str] = []
            analysis_lines.append(f"FILE: {rp}")
            analysis_lines.append(f"SIZE: {info['size']} bytes")
            analysis_lines.append(f"LINES: {info['lines']}")
            analysis_lines.append(f"SHA256: {info['sha256']}")
            analysis_lines.append(f"PURPOSE (heuristic): {info['purpose_guess']}")
            analysis_lines.append("")

            if p.suffix == ".py":
                try:
                    sym = parse_python_symbols(txt)
                    info["python"] = {
                        "module_doc": sym["module_doc"],
                        "imports_count": len(sym["imports"]),
                        "globals_count": len(sym["globals"]),
                        "symbols_count": len(sym["symbols"]),
                    }

                    analysis_lines.append("MODULE DOCSTRING (summary):")
                    analysis_lines.append(sym["module_doc"] or "<none>")
                    analysis_lines.append("")

                    analysis_lines.append("IMPORTS:")
                    analysis_lines.extend([f"  - {x}" for x in sym["imports"]] or ["  <none>"])
                    analysis_lines.append("")

                    analysis_lines.append("TOP-LEVEL GLOBALS / CONSTANTS (best-effort):")
                    analysis_lines.extend([f"  - {x}" for x in sym["globals"]] or ["  <none>"])
                    analysis_lines.append("")

                    analysis_lines.append("SYMBOL TREE (classes/functions):")
                    for s in sym["symbols"]:
                        if s.kind == "class":
                            analysis_lines.append(f"  [CLASS] {s.name}" + (f" bases={s.bases}" if s.bases else ""))
                            if s.decorators:
                                analysis_lines.append(f"    decorators: {s.decorators}")
                            if s.doc:
                                analysis_lines.append(f"    doc: {s.doc}")
                            if s.methods:
                                for m in s.methods:
                                    analysis_lines.append(f"    [METHOD] {m.name}{m.signature}{m.returns}")
                                    if m.decorators:
                                        analysis_lines.append(f"      decorators: {m.decorators}")
                                    if m.doc:
                                        analysis_lines.append(f"      doc: {m.doc}")
                                    if m.calls:
                                        analysis_lines.append("      calls:")
                                        for k,v in list(m.calls.items())[:500]:
                                            analysis_lines.append(f"        - {k}  (x{v})")
                        else:
                            analysis_lines.append(f"  [{'ASYNC ' if s.kind=='async_function' else ''}FUNC] {s.name}{s.signature}{s.returns}")
                            if s.decorators:
                                analysis_lines.append(f"    decorators: {s.decorators}")
                            if s.doc:
                                analysis_lines.append(f"    doc: {s.doc}")
                            if s.calls:
                                analysis_lines.append("    calls:")
                                for k,v in list(s.calls.items())[:500]:
                                    analysis_lines.append(f"      - {k}  (x{v})")

                    analysis_lines.append("")
                    analysis_lines.append("MODULE-WIDE CALL HEATMAP (aggregated):")
                    if sym["module_calls"]:
                        for k,v in list(sym["module_calls"].items())[:800]:
                            analysis_lines.append(f"  - {k}  (x{v})")
                    else:
                        analysis_lines.append("  <none>")
                    analysis_lines.append("")

                    # Save full symbol JSON too
                    sym_json_path = (FILES_DIR / (rp.replace("/", "__") + ".symbols.json"))
                    sym_json_path.write_text(json.dumps({
                        "path": rp,
                        "module_doc": sym["module_doc"],
                        "imports": sym["imports"],
                        "globals": sym["globals"],
                        "symbols": [s.__dict__ for s in sym["symbols"]],
                        "module_calls": sym["module_calls"],
                    }, indent=2), encoding="utf-8")
                    info["symbols_json"] = str(sym_json_path.relative_to(OUT))

                except Exception as e:
                    analysis_lines.append(f"[PY PARSE ERROR] {e}")

            elif p.suffix in {".ts",".tsx",".js",".jsx"}:
                exp = parse_ts_exports(txt)
                info["js_ts"] = {"exports_count": len(exp["exports"])}
                analysis_lines.append("EXPORTS (regex-based, best-effort):")
                analysis_lines.extend([f"  - {x}" for x in exp["exports"]] or ["  <none>"])

            # write per-file analysis
            per_file = normalize_out_path_for_file(p)
            per_file.write_text("\n".join(analysis_lines) + "\n", encoding="utf-8")
            info["analysis_txt"] = str(per_file.relative_to(OUT))

        index["files"].append(info)

    # Import graph
    graph = build_import_graph(py_files)
    graph_json = OUT / "IMPORT_GRAPH.json"
    graph_json.write_text(json.dumps({k: sorted(list(v)) for k,v in graph.items()}, indent=2), encoding="utf-8")

    # internal prefixes guess (repo-relative module roots)
    internal_prefixes = ("backend.", "agent.")
    dot = to_dot(graph, internal_prefixes)
    dot_path = OUT / "IMPORT_GRAPH.dot"
    dot_path.write_text(dot, encoding="utf-8")

    index_path = OUT / "INDEX.json"
    index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")

    # Master summary TXT
    summary = OUT / "SUMMARY.txt"
    lines = []
    lines.append(f"ROOT: {ROOT}")
    lines.append(f"FILES_TOTAL: {index['counts']['files_total']}")
    lines.append(f"PY_FILES: {index['counts']['py_files']}")
    lines.append("")
    lines.append("Artifacts:")
    lines.append(f"  - PROJECT_TREE.txt")
    lines.append(f"  - SUMMARY.txt")
    lines.append(f"  - INDEX.json")
    lines.append(f"  - IMPORT_GRAPH.json")
    lines.append(f"  - IMPORT_GRAPH.dot")
    lines.append(f"  - files/*.txt  (per-file analysis)")
    lines.append(f"  - files/*.symbols.json (per-python-file symbol dump)")
    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
PY

ROOT="$ROOT" OUT="$OUT" python "$OUT/repo_introspect.py"
echo "Saved per-file analyses under: $FILES_DIR"
echo "Saved indexes:"
echo " - $OUT/INDEX.json"
echo " - $OUT/SUMMARY.txt"
echo " - $OUT/IMPORT_GRAPH.json"
echo " - $OUT/IMPORT_GRAPH.dot"

section "QUICK INDEX (TOP 80 FILES WITH THEIR PURPOSE GUESSES)"
python - <<PY
import json
from pathlib import Path
idx = json.loads(Path("$OUT/INDEX.json").read_text())
for f in idx["files"][:80]:
    path=f["path"]
    purpose=f.get("purpose_guess","")
    lines=f.get("lines","?")
    size=f.get("size","?")
    print(f"- {path} | lines={lines} size={size} | {purpose}")
PY

section "DONE"
echo "MASTER REPORT: $REPORT"
echo "PROJECT TREE:  $OUT/PROJECT_TREE.txt"
echo "PER-FILE TXT:  $OUT/files/"
echo "IMPORT DOT:    $OUT/IMPORT_GRAPH.dot"
echo "SUMMARY:       $OUT/SUMMARY.txt"

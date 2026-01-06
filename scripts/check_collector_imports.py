from __future__ import annotations

import pathlib
import py_compile
import sys


def main() -> int:
    base = pathlib.Path(__file__).resolve().parents[1]
    collector_dir = base / "sensors" / "collector"
    failures = 0
    for path in sorted(collector_dir.glob("*.py")):
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            failures += 1
            print(f"[collector] failed to compile: {path}")
            print(f"[collector] {exc.msg}")
    if failures:
        print(f"[collector] compile failures: {failures}")
        return 1
    print("[collector] all collector modules compiled successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import pathlib
import py_compile
import re
import sys


def main() -> int:
    base = pathlib.Path(__file__).resolve().parents[1]
    versions = base / "alembic" / "versions"
    failures = 0
    revisions: dict[str, pathlib.Path] = {}
    for path in sorted(versions.glob("*.py")):
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            failures += 1
            print(f"[migrations] failed to compile: {path}")
            print(f"[migrations] {exc.msg}")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            failures += 1
            print(f"[migrations] failed to read: {path}")
            print(f"[migrations] {exc}")
            continue
        match = re.search(r'^\s*revision\s*=\s*[\'"]([^\'"]+)[\'"]', content, re.M)
        if match:
            revision = match.group(1)
            if revision in revisions:
                failures += 1
                print(
                    "[migrations] duplicate revision detected:"
                    f" {revision} in {revisions[revision]} and {path}"
                )
            else:
                revisions[revision] = path
    if failures:
        print(f"[migrations] compile failures: {failures}")
        return 1
    print("[migrations] all migrations compiled successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

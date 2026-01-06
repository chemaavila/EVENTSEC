from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator, Tuple

from state import CollectorState


def iter_new_lines(path: Path, state: CollectorState) -> Iterator[Tuple[str, int]]:
    file_state = state.get(str(path))
    try:
        stat = path.stat()
    except FileNotFoundError:
        return iter([])

    inode = getattr(stat, "st_ino", None)
    offset = file_state.offset

    if file_state.inode and inode and inode != file_state.inode:
        offset = 0
    if offset > stat.st_size:
        offset = 0

    lines: list[str] = []
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        handle.seek(offset)
        for line in handle:
            lines.append(line.rstrip("\n"))
        new_offset = handle.tell()

    state.update(str(path), inode, new_offset)
    for line in lines:
        if line.strip():
            yield line, new_offset

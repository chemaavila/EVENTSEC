from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass
class FileState:
    inode: Optional[int] = None
    offset: int = 0


@dataclass
class CollectorState:
    path: Path
    files: Dict[str, FileState] = field(default_factory=dict)

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        files = payload.get("files", {}) if isinstance(payload, dict) else {}
        for file_path, state in files.items():
            if not isinstance(state, dict):
                continue
            self.files[file_path] = FileState(
                inode=state.get("inode"),
                offset=state.get("offset", 0),
            )

    def save(self) -> None:
        payload = {
            "files": {
                path: {"inode": state.inode, "offset": state.offset}
                for path, state in self.files.items()
            }
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def get(self, file_path: str) -> FileState:
        return self.files.setdefault(file_path, FileState())

    def update(self, file_path: str, inode: Optional[int], offset: int) -> None:
        self.files[file_path] = FileState(inode=inode, offset=offset)
        self.save()

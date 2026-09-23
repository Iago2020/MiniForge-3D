from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


def config_fingerprint(config: dict[str, Any]) -> str:
    payload = json.dumps(
        config,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def file_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def input_fingerprint(paths: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted((item.resolve() for item in paths), key=str):
        digest.update(str(path).encode("utf-8"))
        if path.is_file():
            digest.update(str(path.stat().st_size).encode("ascii"))
            digest.update(file_sha256(path).encode("ascii"))
        else:
            digest.update(b"<missing>")
    return digest.hexdigest()


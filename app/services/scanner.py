import logging
from pathlib import Path
from typing import Iterable, Optional, Iterator

logger = logging.getLogger(__name__)


def normalize_extensions(exts: Optional[Iterable[str]]) -> Optional[set[str]]:
    if not exts:
        return None
    out = set()
    for e in exts:
        e = e.strip().lower()
        if not e:
            continue
        if not e.startswith("."):
            e = "." + e
        out.add(e)
    return out or None


def iter_files(root: Path, extensions: Optional[set[str]] = None) -> Iterator[Path]:
    """
    Yield files under root recursively.
    If extensions is provided, only yield those extensions.
    """
    logger.info("Starting filesystem walk: root=%s extensions=%s", root, extensions)
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if extensions is not None and p.suffix.lower() not in extensions:
            continue
        yield p

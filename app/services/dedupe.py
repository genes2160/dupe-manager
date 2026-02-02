import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FileInfo:
    filename: str
    size_bytes: int
    path: str


def dupe_key(filename: str, size_bytes: int) -> str:
    return f"{filename}|{size_bytes}"


def find_dupes_name_size(files: List[Path]) -> Dict[str, List[FileInfo]]:
    """
    Group files by (filename + size). Return only groups with >1 item.
    """
    buckets: Dict[str, List[FileInfo]] = {}
    for f in files:
        try:
            stat = f.stat()
        except Exception as e:
            logger.warning("Failed to stat file: %s error=%s", f, e)
            continue

        key = dupe_key(f.name, stat.st_size)
        buckets.setdefault(key, []).append(
            FileInfo(filename=f.name, size_bytes=stat.st_size, path=str(f))
        )

    dupes = {k: v for k, v in buckets.items() if len(v) > 1}
    logger.info("Duplicate grouping complete: total_groups=%d dup_groups=%d", len(buckets), len(dupes))
    return dupes

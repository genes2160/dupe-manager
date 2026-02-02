import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def delete_file(path: str) -> tuple[str, str | None]:
    """
    Returns (result, message)
    result: "deleted" | "skipped" | "failed"
    """
    p = Path(path)
    try:
        if not p.exists():
            return "failed", "file not found"
        if not p.is_file():
            return "failed", "not a file"
        p.unlink()
        logger.info("Deleted file: %s", path)
        return "deleted", None
    except Exception as e:
        logger.exception("Delete failed: %s", path)
        return "failed", str(e)

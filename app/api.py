import json
import logging
from datetime import datetime, timezone
from uuid import uuid4
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException

from app.db import get_conn
from app.models import ScanRequest, ScanResponse, ScanStatus, DeleteRequest
from app.redis_client import get_redis
from app.services.scanner import iter_files, normalize_extensions
from app.services.dedupe import find_dupes_name_size
from app.services.delete import delete_file

logger = logging.getLogger(__name__)
router = APIRouter()


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _set_job(redis, scan_id: str, payload: dict):
    if not redis:
        return
    redis.setex(f"job:{scan_id}", 60 * 60 * 24, json.dumps(payload))


def _get_job(redis, scan_id: str) -> dict | None:
    if not redis:
        return None
    raw = redis.get(f"job:{scan_id}")
    return json.loads(raw) if raw else None


def _publish(redis, scan_id: str, payload: dict):
    if not redis:
        return
    redis.publish(f"job-events:{scan_id}", json.dumps(payload))


@router.post("/scan", response_model=ScanResponse)
def start_scan(req: ScanRequest):
    root = Path(req.root_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise HTTPException(status_code=400, detail="root_path must be an existing directory")

    scan_id = str(uuid4())
    exts = normalize_extensions(req.extensions)

    conn = get_conn()
    conn.execute(
        """
        INSERT INTO scan_runs (id, created_at, root_path, extensions, status, total_files, scanned_files, message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            scan_id,
            utcnow_iso(),
            str(root),
            json.dumps(sorted(exts)) if exts else None,
            "running",
            0,
            0,
            "scan started",
        ),
    )
    conn.commit()

    redis = get_redis()
    _set_job(redis, scan_id, {"scan_id": scan_id, "status": "running", "total_files": 0, "scanned_files": 0})
    _publish(redis, scan_id, {"type": "status", "scan_id": scan_id, "status": "running"})

    # NOTE: This runs inline for simplicity.
    # For production: move to background worker (RQ/Celery) and keep FastAPI responsive.
    try:
        files = []
        scanned = 0

        for f in iter_files(root, exts):
            files.append(f)
            scanned += 1
            if scanned % 250 == 0:
                conn.execute(
                    "UPDATE scan_runs SET scanned_files=? WHERE id=?",
                    (scanned, scan_id),
                )
                conn.commit()
                _set_job(redis, scan_id, {"scan_id": scan_id, "status": "running", "total_files": 0, "scanned_files": scanned})
                _publish(redis, scan_id, {"type": "progress", "scan_id": scan_id, "scanned_files": scanned})

        conn.execute(
            "UPDATE scan_runs SET total_files=?, scanned_files=? WHERE id=?",
            (scanned, scanned, scan_id),
        )
        conn.commit()

        dupes = find_dupes_name_size(files)
        found_at = utcnow_iso()

        # store duplicates
        for k, items in dupes.items():
            for it in items:
                conn.execute(
                    """
                    INSERT INTO duplicates (scan_id, found_at, dup_key, filename, size_bytes, path)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (scan_id, found_at, k, it.filename, it.size_bytes, it.path),
                )
        conn.commit()

        conn.execute(
            "UPDATE scan_runs SET status=?, message=? WHERE id=?",
            ("completed", f"scan completed: {len(dupes)} duplicate groups found", scan_id),
        )
        conn.commit()

        _set_job(redis, scan_id, {"scan_id": scan_id, "status": "completed", "total_files": scanned, "scanned_files": scanned})
        _publish(redis, scan_id, {"type": "status", "scan_id": scan_id, "status": "completed"})
        return ScanResponse(scan_id=scan_id, status="completed", message="Scan finished")
    except Exception as e:
        logger.exception("Scan failed scan_id=%s", scan_id)
        conn.execute("UPDATE scan_runs SET status=?, message=? WHERE id=?", ("failed", str(e), scan_id))
        conn.commit()
        _set_job(redis, scan_id, {"scan_id": scan_id, "status": "failed", "message": str(e)})
        _publish(redis, scan_id, {"type": "status", "scan_id": scan_id, "status": "failed", "message": str(e)})
        return ScanResponse(scan_id=scan_id, status="failed", message=str(e))
    finally:
        conn.close()


@router.get("/scan/{scan_id}/status", response_model=ScanStatus)
def scan_status(scan_id: str):
    redis = get_redis()
    job = _get_job(redis, scan_id)

    conn = get_conn()
    row = conn.execute("SELECT * FROM scan_runs WHERE id=?", (scan_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="scan_id not found")

    # prefer redis for freshest progress
    if job:
        return ScanStatus(
            scan_id=scan_id,
            status=job.get("status", row["status"]),
            total_files=int(job.get("total_files", row["total_files"])),
            scanned_files=int(job.get("scanned_files", row["scanned_files"])),
            message=job.get("message", row["message"]),
        )

    return ScanStatus(
        scan_id=scan_id,
        status=row["status"],
        total_files=row["total_files"],
        scanned_files=row["scanned_files"],
        message=row["message"],
    )


@router.get("/scan/{scan_id}/dupes")
def list_dupes(scan_id: str):
    conn = get_conn()
    rows = conn.execute(
        "SELECT dup_key, filename, size_bytes, path FROM duplicates WHERE scan_id=? ORDER BY dup_key, path",
        (scan_id,),
    ).fetchall()
    conn.close()
    if not rows:
        return {"scan_id": scan_id, "groups": []}

    groups = {}
    for r in rows:
        k = r["dup_key"]
        groups.setdefault(k, {"dup_key": k, "filename": r["filename"], "size_bytes": r["size_bytes"], "items": []})
        groups[k]["items"].append({"filename": r["filename"], "size_bytes": r["size_bytes"], "path": r["path"]})

    return {"scan_id": scan_id, "groups": list(groups.values())}


@router.post("/scan/delete")
def delete_selected(req: DeleteRequest):
    conn = get_conn()
    scan = conn.execute("SELECT * FROM scan_runs WHERE id=?", (req.scan_id,)).fetchone()
    if not scan:
        conn.close()
        raise HTTPException(status_code=404, detail="scan_id not found")

    deleted_at = utcnow_iso()
    results = []

    for choice in req.choices:
        p = Path(choice.path)
        filename = p.name
        size_bytes = p.stat().st_size if p.exists() and p.is_file() else 0

        if choice.action == "skip":
            results.append({"path": choice.path, "result": "skipped"})
            conn.execute(
                """
                INSERT INTO deletions (scan_id, deleted_at, path, filename, size_bytes, result, message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (req.scan_id, deleted_at, choice.path, filename, size_bytes, "skipped", "user skipped"),
            )
            continue

        result, message = delete_file(choice.path)
        results.append({"path": choice.path, "result": result, "message": message})

        conn.execute(
            """
            INSERT INTO deletions (scan_id, deleted_at, path, filename, size_bytes, result, message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (req.scan_id, deleted_at, choice.path, filename, size_bytes, result, message),
        )

    conn.commit()
    conn.close()
    return {"scan_id": req.scan_id, "results": results}


@router.get("/scan/{scan_id}/deletions")
def list_deletions(scan_id: str):
    conn = get_conn()
    rows = conn.execute(
        "SELECT deleted_at, path, filename, size_bytes, result, message FROM deletions WHERE scan_id=? ORDER BY id",
        (scan_id,),
    ).fetchall()
    conn.close()
    return {"scan_id": scan_id, "deletions": [dict(r) for r in rows]}


@router.websocket("/ws/scan/{scan_id}")
async def ws_scan(scan_id: str, ws: WebSocket):
    await ws.accept()
    redis = get_redis()
    if not redis:
        await ws.send_json({"type": "error", "message": "Redis disabled; websocket updates unavailable."})
        await ws.close()
        return

    pubsub = redis.pubsub()
    channel = f"job-events:{scan_id}"
    pubsub.subscribe(channel)

    try:
        # send initial state if present
        job = _get_job(redis, scan_id)
        if job:
            await ws.send_json({"type": "status", **job})

        for msg in pubsub.listen():
            if msg.get("type") != "message":
                continue
            data = json.loads(msg["data"])
            await ws.send_json(data)
    except WebSocketDisconnect:
        pass
    finally:
        try:
            pubsub.unsubscribe(channel)
            pubsub.close()
        except Exception:
            pass

# Changelog
All notable changes to this project will be documented here.

## [0.1.0] - Initial
### Added
- Recursive directory scanner with optional extension filter
- Duplicate detection using filename + file size heuristic
- SQLite persistence for scans, duplicate groups, and delete actions
- FastAPI endpoints for:
  - starting scans
  - checking scan status
  - listing duplicate groups
  - deleting selected files
- Redis pub/sub + websocket support for real-time scan progress
- Basic CLI script for triggering scans

---

## [0.1.1] - Documentation
### Added
- Full end-to-end scan lifecycle documentation in README
- Clear explanation of:
  - scan triggering and session lifecycle
  - directory traversal and metadata collection
  - duplicate grouping logic
  - Redis role in progress/status updates
- Documented user action flow (keep / delete / skip)
- Explicit safety guarantees (read-only scan, no auto-delete)
- Known limitations and intentional tradeoffs section
- Roadmap section outlining future enhancements

---

## [0.2.0] - Planned
### Added
- Background job execution (RQ) for non-blocking scans
- Improved progress metrics (estimated totals, finer counters)
- Optional content hashing mode (SHA-256 / MD5) to reduce false positives
- Space-reclaimed statistics per scan
    * File size
    * File path
    * Timestamps (created, modified)
    * Other relevant metadata


## [0.2.1] – Interactive Frontend & Safe Deletion Flow

### Added
- Browser-based frontend (HTML/CSS/JS) mounted via FastAPI
- Visual preview for duplicate files:
  - Images and videos rendered inline
  - Video previews auto-seek to 1s to avoid black frames
- File metadata display:
  - Filename
  - File size (human-readable)
  - Truncated full path with tooltip
  - Parent folder badge
- Duplicate grouping UI with horizontal scrolling
- Per-file selection using checkboxes
  - First file marked as **“Likely original”**
  - Copies pre-selected by default
- Group-level **Delete selected** action
  - Explicit user confirmation via selection
  - No implicit or automatic deletion

### Backend
- New `/api/file` endpoint for secure file preview streaming
- Static frontend served via FastAPI `StaticFiles`
- Extended delete endpoint to support path-based deletion per scan

### Safety & UX
- Deletion scoped strictly to selected files within a scan
- Clear visual distinction between originals and duplicates
- No auto-delete or background cleanup

---


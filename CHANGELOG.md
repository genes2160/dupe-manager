
---

## CHANGELOG.md (versioned workflow)

```md
# Changelog
All notable changes to this project will be documented here.

## [0.1.0] - Initial
### Added
- Recursive scanner with extension filter
- Duplicate detection by filename + size
- SQLite persistence for scans, duplicates, deletions
- FastAPI endpoints for scan/status/list dupes/delete
- Redis pubsub websocket status updates
- CLI script

## [0.2.0] - Planned
### Added
- Background jobs (RQ) for non-blocking scan
- Incremental progress: total estimation, better counters
- Optional hashing mode to reduce false positives

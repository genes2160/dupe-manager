# Dupe Manager (filename + size)

Find duplicate files (fast heuristic) and manage deletions through a FastAPI backend.

## What it does
- Recursively scans a chosen directory
- Optional extension filter (e.g. only `pdf`)
- Finds duplicates using `(filename + size_bytes)`
- Stores:
  - scan runs (timestamp, root, status)
  - duplicates found (timestamp, group key, file info)
  - deletions and skips (timestamp, result, message)
- Provides API endpoints + websocket status updates (Redis)

> Note: filename+size can produce false positives. Consider adding content hashing later.

## Setup

### 1) Create venv + install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

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


## 🔁 How Dupe-Manager Works (End-to-End Flow)

Dupe-Manager is a **backend-first duplicate file detection service**.
It scans directories, detects potential duplicates, groups them, and allows controlled actions (delete / keep / skip), while reporting progress in real time.

---

## 🧠 High-Level Flow

```
Client → API → File Scanner → Duplicate Grouper → Action Handler
                  ↓
               Redis (progress & status)
```

---

## 1️⃣ Scan Request (Trigger)

A client (CLI, UI, or HTTP tool like Postman) sends a request to **start a scan**.

What the client provides:

* Root directory to scan
* Optional file extensions (e.g. `.pdf`, `.jpg`)
* Optional scan options (depth, exclusions, etc.)

What happens:

* A new **scan session** is created
* A unique scan ID is generated
* Scan status is initialized in Redis

---

## 2️⃣ Directory Traversal

The scanner:

* Walks the directory **recursively**
* Collects metadata for each file:

  * File name
  * File size
  * File path
  * Extension

At this stage:

* No files are modified
* Everything is **read-only**
* Progress updates are pushed to Redis

---

## 3️⃣ Duplicate Detection (Heuristic Phase)

Files are grouped using a **heuristic rule**:

```
Duplicate candidate = same filename + same file size
```

This keeps the scan:

* Fast
* Memory-efficient
* Safe for large directories

⚠️ Important note:
This method may produce **false positives**.
Two different files *can* share the same name and size.

The README explicitly encourages future improvement using:

* Content hashing (SHA-256 / MD5)
* Chunk hashing for large files

---

## 4️⃣ Duplicate Grouping

Once scanning completes:

* Files are grouped into **duplicate sets**
* Each group represents files that *might* be duplicates
* Groups with only one file are discarded

Example group:

```
Group A:
- /docs/report.pdf
- /backup/report.pdf
- /old/report.pdf
```

These groups are returned via the API.

---

## 5️⃣ Real-Time Progress & Status (Redis)

Throughout the scan:

* Progress is written to Redis
* Status includes:

  * Files scanned
  * Groups found
  * Current phase (scanning / grouping / done)
  * Errors (if any)

This enables:

* WebSocket streaming
* Live UI updates
* CLI progress bars

---

## 6️⃣ User Decision Phase

For each duplicate group, the client can:

* ✅ Keep one file
* 🗑️ Delete selected files
* ⏭️ Skip the group entirely

No automatic deletion happens by default.
**All destructive actions are explicit.**

---

## 7️⃣ Action Execution

When an action is submitted:

* The backend validates the request
* File paths are checked again for safety
* The requested action is performed

Possible actions:

* Delete file(s)
* Mark group as resolved
* Ignore group

Actions are:

* Logged
* Traceable per scan
* Isolated per group

---

## 8️⃣ Final Scan State

At completion:

* Scan is marked as `DONE`
* Final statistics are available:

  * Total files scanned
  * Total duplicate groups
  * Files deleted
  * Space recovered (future extension)

Scan history can be stored or discarded depending on setup.

---

## 🔒 Safety Guarantees

* No automatic deletion
* No write operations during scanning
* Explicit user confirmation for destructive actions
* Path-based validation before delete
* Stateless API with Redis-backed progress

---

## 🚧 Known Limitations (Intentional)

* Duplicate detection is heuristic-based (name + size)
* No hashing yet
* No frontend included (API-first design)
* No filesystem locking (read-only scanning)

These are **deliberate tradeoffs** for speed, simplicity, and extensibility.

---

## 🔮 Planned / Easy Extensions

* Content hashing (SHA-256)
* Partial hashing for large files
* File similarity (images / audio)
* UI dashboard
* Dry-run vs destructive modes
* Scan scheduling
* Scan history persistence

---

## Setup

### 1) Create venv + install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

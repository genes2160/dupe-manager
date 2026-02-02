let currentScanId = null;

function formatBytes(bytes) {
  if (!bytes) return "0 B";
  const mb = bytes / (1024 * 1024);
  return mb >= 1 ? `${mb.toFixed(2)} MB` : `${bytes} B`;
}

function shortPath(path, max = 40) {
  if (path.length <= max) return path;
  return "…" + path.slice(path.length - max);
}

function parentFolder(path) {
  const parts = path.replace(/\\/g, "/").split("/");
  return parts.length > 1 ? parts[parts.length - 2] : "";
}

async function startScan() {
  const path = document.getElementById("path").value;
  const extRaw = document.getElementById("extensions").value;

  const extensions = extRaw
    ? extRaw.split(",").map(e => e.trim())
    : [];

  const res = await fetch("/scan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ root_path: path, extensions })    
  });

  const data = await res.json();
  currentScanId = data.scan_id;

  logStatus("Scan started: " + currentScanId);
  pollStatus();
}

async function pollStatus() {
  if (!currentScanId) return;

  const res = await fetch(`/scan/${currentScanId}/status`);
  const data = await res.json();

  logStatus(JSON.stringify(data, null, 2));

  if (data.status !== "completed") {
    setTimeout(pollStatus, 1500);
  } else {
    loadDupes();
  }
}

function isVideo(path) {
  return /\.(mp4|webm|ogg|mkv|avi)$/i.test(path);
}

function isImage(path) {
  return /\.(jpg|jpeg|png|gif|webp)$/i.test(path);
}

async function loadDupes() {
  if (!currentScanId) return;

  const res = await fetch(`/scan/${currentScanId}/dupes`);
  const data = await res.json();

  const groups = data.groups; // ✅ unwrap correctly

  const container = document.getElementById("dupes");
  container.innerHTML = "";

  if (!groups || !groups.length) {
    container.textContent = "No duplicates found.";
    return;
  }

  groups.forEach(group => {
    const groupDiv = document.createElement("div");
    groupDiv.className = "group";

    const filesRow = document.createElement("div");
    filesRow.className = "files";

    group.items.forEach((item, idx) => { // ✅ items, not files
        const card = document.createElement("div");
        card.className = "file-card";

        const filePath = item.path;
        // checkbox
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.checked = idx !== 0; // keep first, select others by default
        checkbox.dataset.path = item.path;

        const checkboxWrap = document.createElement("div");
        checkboxWrap.className = "file-select";
        checkboxWrap.appendChild(checkbox);

        card.appendChild(checkboxWrap);
        if (isVideo(filePath)) {
                const video = document.createElement("video");
                video.src = `/api/file?path=${encodeURIComponent(filePath)}`;
                video.controls = true;
                video.preload = "metadata";

                // ⏩ jump forward to avoid black first frame
                video.addEventListener("loadedmetadata", () => {
                try {
                    if (video.duration > 1) {
                    video.currentTime = 1;
                    }
                } catch (e) {
                    // some browsers block seek until user interaction — safe to ignore
                }
                });

                card.appendChild(video);
                video.muted = true;     // avoids autoplay warnings if you later add it
                video.playsInline = true;
                // video.style.maxHeight = "160px";


        } else if (isImage(filePath)) {
            const img = document.createElement("img");
            img.src = `/api/file?path=${encodeURIComponent(filePath)}`;
            card.appendChild(img);

        } else {
            const placeholder = document.createElement("div");
            placeholder.textContent = "📄";
            placeholder.style.fontSize = "48px";
            card.appendChild(placeholder);
        }

        const meta = document.createElement("div");
        meta.className = "file-meta";

        const name = document.createElement("div");
        name.className = "file-name";
        name.textContent = item.filename;

        const size = document.createElement("div");
        size.className = "file-size";
        size.textContent = `📦 ${formatBytes(item.size_bytes)}`;

        const pathInfo = document.createElement("div");
        pathInfo.className = "file-path";
        pathInfo.textContent = shortPath(item.path);
        pathInfo.title = item.path; // full path on hover

        meta.appendChild(name);
        meta.appendChild(size);
        meta.appendChild(pathInfo);
        const badgeRow = document.createElement("div");
        badgeRow.className = "file-badges";

        const indexBadge = document.createElement("span");
        indexBadge.className = "badge index";
        indexBadge.textContent = `#${idx + 1}`;

        const folderBadge = document.createElement("span");
        folderBadge.className = "badge folder";
        folderBadge.textContent = parentFolder(item.path);

        // optional heuristic: first item = likely original
        const roleBadge = document.createElement("span");
        roleBadge.className = "badge role";
        roleBadge.textContent = idx === 0 ? "Likely original" : "Copy";

        badgeRow.appendChild(indexBadge);
        badgeRow.appendChild(folderBadge);
        badgeRow.appendChild(roleBadge);

        card.appendChild(badgeRow);

        card.appendChild(meta);


        filesRow.appendChild(card);

    });

    // 👇 ADD HERE (ONCE per group)
    const deleteBtn = document.createElement("button");
    deleteBtn.textContent = "🗑️ Delete selected";
    deleteBtn.className = "delete";

    deleteBtn.onclick = async () => {
    const checked = groupDiv.querySelectorAll(
        'input[type="checkbox"]:checked'
    );

    if (!checked.length) {
        alert("No files selected");
        return;
    }

    const paths = Array.from(checked).map(c => c.dataset.path);

    await fetch("/scan/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
        scan_id: currentScanId,
        paths
        })
    });

    loadDupes();
    };

    groupDiv.appendChild(deleteBtn);
    groupDiv.appendChild(filesRow);
    container.appendChild(groupDiv);
  });
}


async function deleteGroup(groupId) {
  await fetch(`/scan/delete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ group_id: groupId })
  });

  loadDupes();
}


function logStatus(text) {
  document.getElementById("status").textContent = text;
}

async function refreshScans() {
  const res = await fetch("/scans");
  const data = await res.json();

  const scans = data.scans;

  const select = document.getElementById("scanSelect");
  select.innerHTML = `<option value="">-- select scan --</option>`;

  if (!scans || !scans.length) return;

  scans.forEach(scan => {
    const opt = document.createElement("option");
    opt.value = scan.scan_id;
    opt.textContent = `${scan.scan_id} (${scan.root_path})`;
    select.appendChild(opt);
  });
}




function selectScan(scanId) {
  if (!scanId) return;

  currentScanId = scanId;
  loadDupes();
}

refreshScans();
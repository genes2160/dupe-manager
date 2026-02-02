import argparse
from pathlib import Path
from app.services.scanner import iter_files, normalize_extensions
from app.services.dedupe import find_dupes_name_size


def main():
    parser = argparse.ArgumentParser(description="Scan for duplicates by filename+size")
    parser.add_argument("root", help="Root directory to scan")
    parser.add_argument("--ext", nargs="*", default=None, help="Extensions, e.g. pdf txt .docx")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    exts = normalize_extensions(args.ext)

    files = list(iter_files(root, exts))
    dupes = find_dupes_name_size(files)

    print(f"Scanned files: {len(files)}")
    print(f"Duplicate groups: {len(dupes)}")
    for k, items in dupes.items():
        print("\n===", k, "===")
        for it in items:
            print(f"  - {it.path} ({it.size_bytes} bytes)")


if __name__ == "__main__":
    main()

"""Core functions for the File Integrity Monitoring System."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
REPORTS_DIR = PROJECT_DIR / "reports"
BASELINE_PATH = DATA_DIR / "baseline.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    """Return a SHA-256 digest without loading the entire file into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_excluded(path: Path, root: Path, exclusions: Iterable[str]) -> bool:
    rel = path.relative_to(root).as_posix()
    for item in exclusions:
        item_norm = str(item).replace("\\", "/").strip("/")
        if rel == item_norm or rel.startswith(item_norm + "/") or path.name == item:
            return True
    return False


def collect_files(folder: str | Path, exclusions: Iterable[str] = ()) -> tuple[dict, list]:
    """Collect metadata and hashes for all readable regular files under folder."""
    root = Path(folder).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Folder does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Not a folder: {root}")

    records = {}
    errors = []
    for current, dirs, names in os.walk(root):
        current_path = Path(current)
        # Prune excluded directories so their contents are not visited.
        dirs[:] = [
            d for d in dirs
            if not _is_excluded(current_path / d, root, exclusions)
        ]
        for name in names:
            path = current_path / name
            if _is_excluded(path, root, exclusions):
                continue
            try:
                if path.is_symlink() or not path.is_file():
                    continue
                rel = path.relative_to(root).as_posix()
                stat = path.stat()
                records[rel] = {
                    "sha256": sha256_file(path),
                    "size_bytes": stat.st_size,
                    "modified_time": datetime.fromtimestamp(
                        stat.st_mtime, timezone.utc
                    ).isoformat(timespec="seconds"),
                }
            except (OSError, PermissionError) as exc:
                errors.append({"path": str(path), "error": str(exc)})
    return records, errors


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    temp_path.replace(path)


def create_baseline(folder: str | Path, exclusions: Iterable[str] = ()) -> dict:
    root = Path(folder).expanduser().resolve()
    records, errors = collect_files(root, exclusions)
    baseline = {
        "project": "File Integrity Monitoring System",
        "created_at_utc": utc_now(),
        "root_folder": str(root),
        "algorithm": "SHA-256",
        "file_count": len(records),
        "excluded": list(exclusions),
        "files": records,
        "collection_errors": errors,
    }
    save_json(BASELINE_PATH, baseline)
    return baseline


def load_baseline() -> dict:
    if not BASELINE_PATH.exists():
        raise FileNotFoundError(
            f"No baseline found at {BASELINE_PATH}. Create one with the baseline command first."
        )
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def scan_folder(folder: str | Path, exclusions: Iterable[str] = ()) -> dict:
    root = Path(folder).expanduser().resolve()
    baseline = load_baseline()
    baseline_root = Path(baseline["root_folder"]).resolve()
    if root != baseline_root:
        raise ValueError(
            "The selected folder does not match the baseline folder.\n"
            f"Baseline: {baseline_root}\nSelected: {root}\n"
            "Create a new baseline for this folder if that is intentional."
        )

    current, errors = collect_files(root, exclusions or baseline.get("excluded", []))
    original = baseline.get("files", {})
    original_names, current_names = set(original), set(current)

    added = sorted(current_names - original_names)
    deleted = sorted(original_names - current_names)
    modified = sorted(
        name for name in original_names & current_names
        if original[name].get("sha256") != current[name].get("sha256")
    )
    unchanged = sorted(
        name for name in original_names & current_names
        if original[name].get("sha256") == current[name].get("sha256")
    )

    report = {
        "project": "File Integrity Monitoring System",
        "scan_time_utc": utc_now(),
        "root_folder": str(root),
        "algorithm": "SHA-256",
        "summary": {
            "baseline_files": len(original),
            "current_files": len(current),
            "modified_count": len(modified),
            "new_count": len(added),
            "deleted_count": len(deleted),
            "unchanged_count": len(unchanged),
            "error_count": len(errors),
            "status": "CHANGES DETECTED" if (modified or added or deleted or errors) else "NO CHANGES",
        },
        "modified": [{"path": p, "old_sha256": original[p]["sha256"], "new_sha256": current[p]["sha256"]} for p in modified],
        "new": [{"path": p, "sha256": current[p]["sha256"]} for p in added],
        "deleted": [{"path": p, "old_sha256": original[p]["sha256"]} for p in deleted],
        "unchanged": unchanged,
        "errors": errors,
    }
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_DIR / f"scan_report_{stamp}.json"
    save_json(report_path, report)
    report["report_file"] = str(report_path)
    save_json(REPORTS_DIR / "latest_report.json", report)
    return report


def load_report(report_file: str | Path | None = None) -> dict:
    path = Path(report_file) if report_file else REPORTS_DIR / "latest_report.json"
    if not path.is_absolute():
        path = (PROJECT_DIR / path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Report not found: {path}. Run a scan first.")
    return json.loads(path.read_text(encoding="utf-8"))

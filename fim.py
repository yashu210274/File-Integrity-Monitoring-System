"""Command-line interface for File Integrity Monitoring System."""
import argparse
import json
import sys
from pathlib import Path

from fim_core import create_baseline, scan_folder, load_report


def print_report(report: dict) -> None:
    summary = report.get("summary", {})
    print("\n=== FILE INTEGRITY MONITORING REPORT ===")
    print(f"Status          : {summary.get('status', 'N/A')}")
    print(f"Folder          : {report.get('root_folder', 'N/A')}")
    print(f"Baseline files  : {summary.get('baseline_files', 'N/A')}")
    print(f"Current files   : {summary.get('current_files', 'N/A')}")
    print(f"Modified        : {summary.get('modified_count', 0)}")
    print(f"New             : {summary.get('new_count', 0)}")
    print(f"Deleted         : {summary.get('deleted_count', 0)}")
    print(f"Unchanged       : {summary.get('unchanged_count', 0)}")
    print(f"Read errors     : {summary.get('error_count', 0)}")

    for key, label in (("modified", "MODIFIED FILES"), ("new", "NEW FILES"), ("deleted", "DELETED FILES")):
        items = report.get(key, [])
        if items:
            print(f"\n{label}:")
            for item in items:
                print(f"  - {item['path']}")
    if report.get("errors"):
        print("\nREAD ERRORS:")
        for item in report["errors"]:
            print(f"  - {item['path']}: {item['error']}")
    if report.get("report_file"):
        print(f"\nReport saved to: {report['report_file']}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect modified, new, and deleted files using SHA-256 hashes."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    baseline_parser = sub.add_parser("baseline", help="Create or replace the baseline for a folder")
    baseline_parser.add_argument("folder", help="Folder to monitor")
    baseline_parser.add_argument("--exclude", action="append", default=[], help="Relative path or file/directory name to exclude (repeatable)")

    scan_parser = sub.add_parser("scan", help="Compare a folder with the saved baseline")
    scan_parser.add_argument("folder", help="Folder to scan")
    scan_parser.add_argument("--exclude", action="append", default=[], help="Relative path or file/directory name to exclude (repeatable)")

    report_parser = sub.add_parser("report", help="Print the latest scan report")
    report_parser.add_argument("--file", help="Path to a JSON report file")

    args = parser.parse_args()
    try:
        if args.command == "baseline":
            baseline = create_baseline(args.folder, args.exclude)
            print("Baseline created successfully.")
            print(f"Folder: {baseline['root_folder']}")
            print(f"Files recorded: {baseline['file_count']}")
            print(f"Baseline file: {Path(__file__).resolve().parent / 'data' / 'baseline.json'}")
            if baseline["collection_errors"]:
                print(f"Warning: {len(baseline['collection_errors'])} file(s) could not be read.")
        elif args.command == "scan":
            report = scan_folder(args.folder, args.exclude)
            print_report(report)
        elif args.command == "report":
            print_report(load_report(args.file))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

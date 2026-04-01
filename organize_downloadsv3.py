"""
organize_downloadsv3.py

Interactive Downloads organizer with backup and run history support.

What this script provides:
- Categorize files into folders by extension
- Create a backup copy of each file before moving
- Record move metadata (original path, moved path, backup path, status)
- Undo the most recent successful run
- Simple user interface (menu) and CLI flags
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Path to the current user's Downloads directory.
DEFAULT_DOWNLOADS_PATH = Path.home() / "Downloads"
DEFAULT_DOWNLOADS_PATH.mkdir(parents=True, exist_ok=True)
PROJECT_ROOT = Path(__file__).resolve().parent

# File extension groups used for folder categorization.
FILE_TYPES: dict[str, list[str]] = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".tiff"],
    "Documents": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".csv", ".rtf"],
    "Videos": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm"],
    "Music": [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "Programs": [".exe", ".msi", ".bat", ".cmd", ".ps1"],
    "Others": [],
}

# Runtime data and logs are always stored in this project folder.
PROJECT_DATA_DIR = PROJECT_ROOT / "downloads_backup_data" / ".organizer_data"
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


def _paths(base_dir: Path) -> dict[str, Path]:
    """Return runtime paths for organizer state storage."""
    data_dir = PROJECT_DATA_DIR
    backup_root = data_dir / "backups"
    runs_file = data_dir / "runs_history.json"
    log_file = data_dir / "organize_log.txt"
    last_run_pointer = data_dir / "last_run_id.txt"
    return {
        "base": base_dir,
        "data_dir": data_dir,
        "backup_root": backup_root,
        "runs_file": runs_file,
        "log_file": log_file,
        "last_run_pointer": last_run_pointer,
    }


def _ensure_runtime_dirs(paths: dict[str, Path]) -> None:
    """Create all required runtime directories for organizer state."""
    paths["base"].mkdir(parents=True, exist_ok=True)
    paths["data_dir"].mkdir(parents=True, exist_ok=True)
    paths["backup_root"].mkdir(parents=True, exist_ok=True)


def _configure_file_logging(log_file: Path) -> None:
    """Attach a file handler once so actions are persisted on disk."""
    logger = logging.getLogger()
    target = str(log_file.resolve())
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler) and handler.baseFilename == target:
            return
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    logger.addHandler(file_handler)


def _load_runs(runs_file: Path) -> list[dict[str, Any]]:
    """Load run history from disk."""
    if not runs_file.exists():
        return []
    try:
        with runs_file.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        logging.warning("Unable to read runs history file. Starting fresh.")
        return []


def _save_runs(runs: list[dict[str, Any]], runs_file: Path) -> None:
    """Persist run history to disk."""
    with runs_file.open("w", encoding="utf-8") as file:
        json.dump(runs, file, indent=2)


def _new_run_id() -> str:
    """Return a unique run id based on timestamp."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_category(extension: str) -> str:
    """Return the category name for a given file extension."""
    for category, extensions in FILE_TYPES.items():
        if extension.lower() in extensions:
            return category
    return "Others"


def _backup_file(source: Path, run_backup_dir: Path) -> Path:
    """Create a backup copy of source file and return backup path."""
    run_backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = run_backup_dir / source.name

    # Ensure backup filename stays unique if name already exists.
    counter = 1
    while backup_path.exists():
        backup_path = run_backup_dir / f"{source.stem}_{counter}{source.suffix}"
        counter += 1

    shutil.copy2(source, backup_path)
    return backup_path


def organize_downloads(base_dir: Path, create_backup: bool = True, dry_run: bool = False) -> dict[str, Any]:
    """
    Move files from Downloads into category folders and record metadata.

    Args:
        create_backup: When True, copy files to backup storage before move.
        dry_run: When True, only preview actions and do not move/copy files.

    Returns:
        dict: run metadata including moved files and backup paths.
    """
    runtime = _paths(base_dir)
    _ensure_runtime_dirs(runtime)
    backup_root = runtime["backup_root"]
    runs_file = runtime["runs_file"]
    log_file = runtime["log_file"]
    last_run_pointer = runtime["last_run_pointer"]
    _configure_file_logging(log_file)

    run_id = _new_run_id()
    started_at = datetime.now().isoformat(timespec="seconds")
    run_backup_dir = backup_root / run_id
    records: list[dict[str, Any]] = []

    for item in base_dir.iterdir():
        # Process files only. Existing directories are intentionally untouched.
        if not item.is_file():
            continue

        # Skip script metadata artifacts.
        if item.name.startswith(".organizer_data"):
            continue

        extension = item.suffix.lower()
        category = get_category(extension)
        destination_folder = base_dir / category
        destination_folder.mkdir(parents=True, exist_ok=True)
        destination_path = destination_folder / item.name

        record: dict[str, Any] = {
            "file_name": item.name,
            "original_path": str(item),
            "category": category,
            "moved_path": str(destination_path),
            "backup_path": None,
            "status": "pending",
        }

        if destination_path.exists():
            record["status"] = "skipped_destination_exists"
            records.append(record)
            logging.info("[%s] Skipped %s; destination exists in %s", base_dir, item.name, category)
            continue

        try:
            if dry_run:
                record["status"] = "would_move"
                if create_backup:
                    record["backup_path"] = str(run_backup_dir / item.name)
                logging.info("[%s] Dry run: %s would move to %s", base_dir, item.name, category)
            else:
                if create_backup:
                    backup_path = _backup_file(item, run_backup_dir)
                    record["backup_path"] = str(backup_path)

                shutil.move(str(item), str(destination_path))
                record["status"] = "moved"
                logging.info("[%s] Moved %s to %s", base_dir, item.name, category)
        except OSError as error:
            record["status"] = f"error: {error}"
            logging.exception("[%s] Failed to process %s", base_dir, item.name)

        records.append(record)

    summary = {
        "run_id": run_id,
        "started_at": started_at,
        "downloads_path": str(base_dir),
        "backup_directory": str(run_backup_dir) if create_backup else None,
        "log_file": str(log_file),
        "backup_enabled": create_backup,
        "dry_run": dry_run,
        "records": records,
    }

    runs = _load_runs(runs_file)
    runs.append(summary)
    _save_runs(runs, runs_file)
    if not dry_run:
        last_run_pointer.write_text(run_id, encoding="utf-8")
    return summary


def undo_last_move(base_dir: Path) -> bool:
    """Undo moved files from the most recent run."""
    runtime = _paths(base_dir)
    _ensure_runtime_dirs(runtime)
    runs_file = runtime["runs_file"]
    runs = _load_runs(runs_file)
    if not runs:
        print("No run history found.")
        return False

    last_run = runs[-1]
    records = last_run.get("records", [])
    undone_count = 0

    for record in records:
        if record.get("status") != "moved":
            continue

        moved_path = Path(record["moved_path"])
        original_path = Path(record["original_path"])
        if moved_path.exists():
            original_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(moved_path), str(original_path))
            record["status"] = "undone"
            undone_count += 1
            logging.info("[%s] Undo move: %s -> %s", base_dir, moved_path, original_path)

    last_run["undo_completed_at"] = datetime.now().isoformat(timespec="seconds")
    _save_runs(runs, runs_file)
    print(f"Undo completed. Restored {undone_count} file(s).")
    return True


def print_last_run_summary(base_dir: Path) -> None:
    """Print compact details of the most recent run."""
    runtime = _paths(base_dir)
    _ensure_runtime_dirs(runtime)
    runs_file = runtime["runs_file"]
    runs = _load_runs(runs_file)
    if not runs:
        print("No run history available.")
        return

    run = runs[-1]
    records = run.get("records", [])
    moved = sum(1 for record in records if record.get("status") == "moved")
    skipped = sum(1 for record in records if str(record.get("status", "")).startswith("skipped"))
    errored = sum(1 for record in records if str(record.get("status", "")).startswith("error"))

    print("\nLast Run Summary")
    print("----------------")
    print(f"Run ID          : {run.get('run_id')}")
    print(f"Started At      : {run.get('started_at')}")
    print(f"Backup Directory: {run.get('backup_directory')}")
    print(f"Moved           : {moved}")
    print(f"Skipped         : {skipped}")
    print(f"Errors          : {errored}")
    print(f"History File    : {runs_file}")


def schedule_run(base_dir: Path, interval_minutes: int, create_backup: bool = True) -> None:
    """Run organizer repeatedly at fixed minute intervals."""
    if interval_minutes <= 0:
        print("Interval must be greater than 0.")
        return

    print(f"Scheduler started: every {interval_minutes} minute(s). Press Ctrl+C to stop.")
    try:
        while True:
            result = organize_downloads(base_dir=base_dir, create_backup=create_backup)
            moved = sum(1 for record in result["records"] if record["status"] == "moved")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Run {result['run_id']} moved {moved} file(s).")
            time.sleep(interval_minutes * 60)
    except KeyboardInterrupt:
        print("\nScheduler stopped.")


def interactive_menu(base_dir: Path) -> None:
    """Simple text-based UI for common actions."""
    menu = """
Downloads Organizer
-------------------
1) Organize now (with backup)
2) Organize now (without backup)
3) Preview dry run (with backup paths)
4) Undo last run
5) Show last run summary
6) Start scheduler
7) Exit
"""
    while True:
        print(menu)
        choice = input("Choose an option [1-7]: ").strip()

        if choice == "1":
            result = organize_downloads(base_dir=base_dir, create_backup=True)
            moved = sum(1 for record in result["records"] if record["status"] == "moved")
            print(f"Completed run {result['run_id']}. Moved {moved} file(s).")
        elif choice == "2":
            result = organize_downloads(base_dir=base_dir, create_backup=False)
            moved = sum(1 for record in result["records"] if record["status"] == "moved")
            print(f"Completed run {result['run_id']}. Moved {moved} file(s).")
        elif choice == "3":
            result = organize_downloads(base_dir=base_dir, create_backup=True, dry_run=True)
            previews = [record for record in result["records"] if record["status"] == "would_move"]
            print(f"Dry run {result['run_id']} preview count: {len(previews)}")
            for record in previews:
                print(f"- {record['file_name']} -> {record['category']}")
        elif choice == "4":
            undo_last_move(base_dir=base_dir)
        elif choice == "5":
            print_last_run_summary(base_dir=base_dir)
        elif choice == "6":
            value = input("Run every how many minutes? ").strip()
            if not value.isdigit():
                print("Please enter a whole number.")
                continue
            schedule_run(base_dir=base_dir, interval_minutes=int(value), create_backup=True)
        elif choice == "7":
            print("Goodbye.")
            break
        else:
            print("Invalid choice. Please select a value from 1 to 7.")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Organize Downloads with backup + history tracking.")
    parser.add_argument("--menu", action="store_true", help="Open interactive menu.")
    parser.add_argument("--run", action="store_true", help="Run organizer once.")
    parser.add_argument("--undo", action="store_true", help="Undo the most recent run.")
    parser.add_argument("--status", action="store_true", help="Show last run summary.")
    parser.add_argument("--no-backup", action="store_true", help="Run without creating file backups.")
    parser.add_argument("--dry-run", action="store_true", help="Preview moves without changing files.")
    parser.add_argument("--schedule", type=int, default=0, help="Run organizer every N minutes.")
    parser.add_argument(
        "--path",
        type=str,
        default=str(DEFAULT_DOWNLOADS_PATH),
        help="Target folder to organize (default: ~/Downloads).",
    )
    return parser.parse_args()


def main() -> None:
    """Program entry point."""
    args = parse_args()
    base_dir = Path(args.path).expanduser().resolve()

    if args.menu:
        interactive_menu(base_dir=base_dir)
        return

    if args.undo:
        undo_last_move(base_dir=base_dir)
        return

    if args.status:
        print_last_run_summary(base_dir=base_dir)
        return

    if args.schedule > 0:
        schedule_run(base_dir=base_dir, interval_minutes=args.schedule, create_backup=not args.no_backup)
        return

    # Default behavior for direct execution is a single run.
    if args.run or (not any([args.menu, args.undo, args.status, args.schedule])):
        result = organize_downloads(base_dir=base_dir, create_backup=not args.no_backup, dry_run=args.dry_run)
        moved = sum(1 for record in result["records"] if record["status"] == "moved")
        preview = sum(1 for record in result["records"] if record["status"] == "would_move")
        if args.dry_run:
            print(f"Dry run complete. Run ID: {result['run_id']} | Preview moves: {preview}")
            for record in result["records"]:
                if record["status"] == "would_move":
                    print(f"- {record['file_name']} -> {record['category']} | dest: {record['moved_path']}")
        else:
            print(f"Downloads organized. Run ID: {result['run_id']} | Moved files: {moved}")
        print(f"History saved to: {PROJECT_DATA_DIR / 'runs_history.json'}")


if __name__ == "__main__":
    main()
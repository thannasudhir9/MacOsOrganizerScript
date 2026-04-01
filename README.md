# MacOS Downloads Folder Organizer
Date : 10 June 2025

A bash script that automatically organizes files in your macOS Downloads folder by categorizing them into appropriate directories based on their file types.

## Features

- Automatically creates category-specific folders if they don't exist
- Organizes files into the following categories:
  - Images (.jpg, .jpeg, .png, .gif, .bmp, .tiff, .webp, .svg, etc.)
  - Documents (.pdf, .doc, .docx, .txt, .rtf, .pages, etc.)
  - Logs (.log, .apex, .trace, .debug)
  - Videos (.mp4, .avi, .mkv, .mov, .wmv, etc.)
  - Audio (.mp3, .wav, .flac, .aac, .ogg, etc.)
  - Archives (.zip, .rar, .7z, .tar, .gz, etc.)
  - Applications (.app, .pkg, .dmg, .exe, etc.)
  - Code (.js, .html, .css, .py, .java, etc.)
  - Spreadsheets (.xls, .xlsx, .csv, .numbers)
  - Presentations (.ppt, .pptx, .key)
  - Ebooks (.epub, .mobi, .azw)
  - Fonts (.ttf, .otf, .woff)
  - Other (uncategorized files)

## Usage

1. Make the script executable:
```bash
chmod +x organizeFilesInMacOsV3.sh
```

## Python Organizer (Recommended)

Use `organize_downloadsv3.py` for a better user interface and safer file handling.

### Highlights

- Interactive menu mode for non-technical users
- Optional command-line mode for automation
- Backup strategy before move (per-run backup folder)
- Full run history with original path, moved path, backup path, and status
- Undo support for the most recent run

### Run Commands

```bash
python3 organize_downloadsv3.py --menu
```

```bash
python3 organize_downloadsv3.py --run
```

```bash
python3 organize_downloadsv3.py --run --dry-run
```

```bash
python3 organize_downloadsv3.py --undo
```

```bash
python3 organize_downloadsv3.py --status
```

```bash
python3 organize_downloadsv3.py --schedule 60
```

### Web App UI

Start the dashboard:

```bash
python3 web_ui.py
```

Open in browser:

`http://127.0.0.1:8080`

From the web app you can:
- Run organizer with backup
- Preview dry run
- Run without backup
- Undo last run
- View recent runs and latest file-level statuses

### Backup + History Storage

Runtime data is stored in:

- `downloads_backup_data/.organizer_data/organize_log.txt`
- `downloads_backup_data/.organizer_data/runs_history.json`
- `downloads_backup_data/.organizer_data/backups/<run_id>/`

Each record in `runs_history.json` stores:

- Original file path
- New moved file path
- Backup file path (if backup enabled)
- Status (`moved`, `skipped_destination_exists`, `error`, `undone`)


## Usage For Windows

# Key Features
Organizes files by type: Moves files into subfolders (e.g., Images, Documents, Videos, etc.) based on their extensions.

Folders untouched: Only files are moved; existing folders are not modified.

Creates subfolders: Automatically creates category folders if they do not exist.

Avoids overwriting: Skips moving files if a file with the same name already exists in the destination.

Undo: Allows you to undo the last organizing action, moving files back to their original locations.

Logging: All actions are logged to organize_log.txt in your Downloads folder.

Scheduled runs: Can be set to organize your Downloads folder automatically at regular intervals.



# Downloads Folder Organizer

This Python script organizes your Windows Downloads folder by moving files into categorized subfolders based on their file types. It includes advanced features like undo, logging, and scheduled runs.

## Features


- **Organizes files by type:** Moves files into subfolders (e.g., Images, Documents, Videos, etc.) based on their extensions.
- **Folders untouched:** Only files are moved; existing folders are not modified.
- **Creates subfolders:** Automatically creates category folders if they do not exist.
- **Avoids overwriting:** Skips moving files if a file with the same name already exists in the destination.
- **Undo:** Allows you to undo the last organizing action, moving files back to their original locations.
- **Logging:** All actions are logged to `organize_log.txt` in your Downloads folder.
- **Scheduled runs:** Can be set to organize your Downloads folder automatically at regular intervals.

## How It Works

1. **Scan:** The script scans your Downloads folder for files.
2. **Categorize:** Each file is categorized based on its extension.
3. **Move:** Files are moved to their respective subfolders.
4. **Log:** Each move is logged for tracking and undo purposes.
5. **Undo:** The script keeps a log of moved files, allowing you to undo the last operation.
6. **Schedule:** You can run the script periodically using the built-in scheduler.

## Usage

1. **Copy the script** to a file, e.g., `organize_downloads.py`.
2. **Open Command Prompt** and navigate to the script's location.
3. **Run the script:**

4. **Undo last move:**
Uncomment and run the `undo_last_move()` function in the script.
5. **Schedule runs:**
Use the `schedule_run(interval_minutes)` function to run the organizer at your chosen interval.

## Code Overview

- `file_types`: Dictionary mapping categories to file extensions.
- `organize_downloads()`: Main function to organize files.
- `undo_last_move()`: Undoes the last organizing action.
- `schedule_run(interval_minutes)`: Runs the organizer periodically.
- Logging is handled by Python's `logging` module.
- Undo information is stored in `undo_log.json`.

## Customization

- Add or remove file extensions in the `file_types` dictionary.
- Change folder names as desired.
- Adjust the scheduling interval as needed.

## Requirements

- Python 3.x
- Works on Windows (should also work on Linux/Mac with path adjustments)

---

**Let me know if you need more features or a different script language!**


Command to Run in Windows to Organize files in Downloads Folder
```bash
python organize_downloadsv3.py
```
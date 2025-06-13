# This script organizes files in the Downloads folder into categorized subfolders based on file types.
# It does not touch any existing folders in the Downloads directory.

# organize_downloadsv3.py
# add extra features like undo, logging, and scheduled runs

import os
import shutil
import logging
import json
import time
import threading

# Set your Downloads folder path
downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads')

# Ensure Downloads folder exists
os.makedirs(downloads_path, exist_ok=True)

# Define file type categories
file_types = {
    'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.tiff'],
    'Documents': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.csv', '.rtf'],
    'Videos': ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.webm'],
    'Music': ['.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a'],
    'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
    'Programs': ['.exe', '.msi', '.bat', '.cmd', '.ps1'],
    'Others': []  # For uncategorized files
}

# Setup logging
log_file = os.path.join(downloads_path, 'organize_log.txt')
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')

# Undo log file
undo_log_file = os.path.join(downloads_path, 'undo_log.json')


def get_category(extension):
    for category, extensions in file_types.items():
        if extension.lower() in extensions:
            return category
    return 'Others'


def organize_downloads():
    moved_files = []
    for item in os.listdir(downloads_path):
        item_path = os.path.join(downloads_path, item)
        # Only process files, skip folders
        if os.path.isfile(item_path):
            ext = os.path.splitext(item)[1]
            category = get_category(ext)
            dest_folder = os.path.join(downloads_path, category)
            os.makedirs(dest_folder, exist_ok=True)
            dest_path = os.path.join(dest_folder, item)
            # Avoid overwriting files
            if not os.path.exists(dest_path):
                shutil.move(item_path, dest_path)
                moved_files.append({'src': item_path, 'dest': dest_path})
                logging.info(f"Moved file {item} to {category}")
            else:
                logging.info(f"File {item} already exists in {category}, skipping.")
    # Save moved files for undo
    if moved_files:
        with open(undo_log_file, 'w') as f:
            json.dump(moved_files, f)
    return moved_files


def undo_last_move():
    if not os.path.exists(undo_log_file):
        print("No undo information found.")
        return
    with open(undo_log_file, 'r') as f:
        moved_files = json.load(f)
    for move in moved_files:
        if os.path.exists(move['dest']):
            shutil.move(move['dest'], move['src'])
            logging.info(f"Undo move: Moved file back from {move['dest']} to {move['src']}")
    os.remove(undo_log_file)
    print("Undo completed.")


def schedule_run(interval_minutes):
    def run_periodically():
        while True:
            organize_downloads()
            time.sleep(interval_minutes * 60)
    thread = threading.Thread(target=run_periodically, daemon=True)
    thread.start()
    print(f"Scheduled organizer to run every {interval_minutes} minutes.")


if __name__ == '__main__':
    organize_downloads()
    print("Downloads folder organized successfully! (Folders untouched)")
    # Uncomment below to undo last move
    # undo_last_move()
    # Uncomment below to schedule runs every 60 minutes
    # schedule_run(60)
# This script organizes files in the Downloads folder into categorized subfolders based on file types.
# It does not touch any existing folders in the Downloads directory.
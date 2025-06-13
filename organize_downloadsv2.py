#remember it should not touch any folders and sort them out under downloads folder

import os
import shutil

# Set your Downloads folder path
downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads')

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

def get_category(extension):
    for category, extensions in file_types.items():
        if extension.lower() in extensions:
            return category
    return 'Others'

def organize_downloads():
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
            else:
                print(f"File {item} already exists in {category}, skipping.")

if __name__ == '__main__':
    organize_downloads()
    print("Downloads folder organized successfully! (Folders untouched)")
# This script organizes files in the Downloads folder into categorized subfolders based on file types.
# It does not touch any existing folders in the Downloads directory.
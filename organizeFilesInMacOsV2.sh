#!/bin/bash

# Navigate to Downloads folder
cd ~/Downloads

echo "Organizing Downloads folder..."

# Create folders if they don't exist
mkdir -p Images
mkdir -p Documents
mkdir -p Logs
mkdir -p Videos
mkdir -p Audio
mkdir -p Archives
mkdir -p Applications
mkdir -p Code
mkdir -p Spreadsheets
mkdir -p Presentations
mkdir -p Ebooks
mkdir -p Fonts
mkdir -p Other

# Function to move files and report
move_files() {
    local pattern="$1"
    local destination="$2"
    local description="$3"
    
    files_moved=$(find . -maxdepth 1 $pattern -print0 2>/dev/null | wc -l | tr -d ' ')
    if [ "$files_moved" -gt 0 ]; then
        find . -maxdepth 1 $pattern -exec mv {} "$destination"/ \; 2>/dev/null
        echo "Moved $description to $destination/"
    fi
}

# Images
move_files "\( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.gif' -o -iname '*.bmp' -o -iname '*.tiff' -o -iname '*.tif' -o -iname '*.webp' -o -iname '*.svg' -o -iname '*.ico' -o -iname '*.heic' -o -iname '*.raw' \)" "Images" "image files"

# Documents (including PDFs)
move_files "\( -iname '*.pdf' -o -iname '*.doc' -o -iname '*.docx' -o -iname '*.txt' -o -iname '*.rtf' -o -iname '*.odt' -o -iname '*.pages' -o -iname '*.tex' -o -iname '*.md' \)" "Documents" "document files"

# Logs (including Apex logs)
move_files "\( -iname '*.log' -o -iname '*.apex' -o -iname '*.apxc' -o -iname '*.trace' -o -iname '*.debug' \)" "Logs" "log files"

# Videos
move_files "\( -iname '*.mp4' -o -iname '*.avi' -o -iname '*.mkv' -o -iname '*.mov' -o -iname '*.wmv' -o -iname '*.flv' -o -iname '*.webm' -o -iname '*.m4v' -o -iname '*.3gp' -o -iname '*.mpg' -o -iname '*.mpeg' \)" "Videos" "video files"

# Audio
move_files "\( -iname '*.mp3' -o -iname '*.wav' -o -iname '*.flac' -o -iname '*.aac' -o -iname '*.ogg' -o -iname '*.wma' -o -iname '*.m4a' -o -iname '*.aiff' \)" "Audio" "audio files"

# Archives
move_files "\( -iname '*.zip' -o -iname '*.rar' -o -iname '*.7z' -o -iname '*.tar' -o -iname '*.gz' -o -iname '*.bz2' -o -iname '*.xz' -o -iname '*.dmg' -o -iname '*.iso' \)" "Archives" "archive files"

# Applications
move_files "\( -iname '*.app' -o -iname '*.pkg' -o -iname '*.deb' -o -iname '*.rpm' -o -iname '*.msi' -o -iname '*.exe' \)" "Applications" "application files"

# Code files
move_files "\( -iname '*.js' -o -iname '*.html' -o -iname '*.css' -o -iname '*.py' -o -iname '*.java' -o -iname '*.cpp' -o -iname '*.c' -o -iname '*.php' -o -iname '*.rb' -o -iname '*.go' -o -iname '*.rs' -o -iname '*.swift' -o -iname '*.kt' -o -iname '*.json' -o -iname '*.xml' -o -iname '*.yaml' -o -iname '*.yml' -o -iname '*.sql' -o -iname '*.sh' -o -iname '*.bat' \)" "Code" "code files"

# Spreadsheets
move_files "\( -iname '*.xls' -o -iname '*.xlsx' -o -iname '*.csv' -o -iname '*.ods' -o -iname '*.numbers' \)" "Spreadsheets" "spreadsheet files"

# Presentations
move_files "\( -iname '*.ppt' -o -iname '*.pptx' -o -iname '*.odp' -o -iname '*.key' \)" "Presentations" "presentation files"

# Ebooks
move_files "\( -iname '*.epub' -o -iname '*.mobi' -o -iname '*.azw' -o -iname '*.azw3' -o -iname '*.fb2' \)" "Ebooks" "ebook files"

# Fonts
move_files "\( -iname '*.ttf' -o -iname '*.otf' -o -iname '*.woff' -o -iname '*.woff2' -o -iname '*.eot' \)" "Fonts" "font files"

# Move any remaining files (excluding folders) to Other
find . -maxdepth 1 -type f ! -name ".*" -exec mv {} Other/ \; 2>/dev/null

# Remove empty folders that were created but not used
rmdir Images Documents Logs Videos Audio Archives Applications Code Spreadsheets Presentations Ebooks Fonts Other 2>/dev/null

echo ""
echo "Organization complete! Check your Downloads folder for the new organized structure."
echo ""
echo "Created folders:"
ls -la | grep "^d" | grep -v "^\.$" | grep -v "^\.\.$" | awk '{print "- " $NF}'
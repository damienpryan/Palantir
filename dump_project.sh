#!/bin/bash

# This script recursively lists all regular files in the current directory
# and outputs their content with clear markers.

START_MARKER="--- FILE_START: "
END_MARKER="--- FILE_END: "
SEPARATOR_MARKER="--- CONTENT_START ---"

echo "--- PROJECT DUMP START ---"
echo ""

# Find all regular files in the current directory and its subdirectories
# -print0 ensures correct handling of filenames with spaces or special characters
find . -type f -print0 | while IFS= read -r -d $'\0' file; do
    # Skip Git internal files
    if [[ "$file" == "./.git/"* ]]; then
        continue
    fi
    # Skip script itself if it's in the directory
    if [[ "$file" == "./dump_project.sh" ]]; then
        continue
    fi

    # Output the file path
    echo "${START_MARKER}${file}"
    echo "${SEPARATOR_MARKER}"

    # Output file content
    cat "$file"

    echo "${END_MARKER}${file}"
    echo "" # Add a blank line for readability between files
done

echo "--- PROJECT DUMP END ---"

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
find . -type f ! -path '*/.env' ! -name '*_dump.txt' -print0 | while IFS= read -r -d $'\0' file;
    # Skip Git internal files
    if [[ "$file" == "./.git/"* ]]; then
        continue
    fi
    # Skip Python bytecode files
    if [[ "$file" == *.pyc ]]; then # Corrected line
        continue
    fi
    # Skip __pycache__ directories (though .pyc exclusion handles files within them)
    if [[ "$file" == *"/__pycache__/"* ]]; then
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
echo "--- About to Git status ---"
git status .
echo "--- end Git status ---"

echo "--- About to Git ls-files ---"
git ls-files
echo "--- end Git ls-files ---"


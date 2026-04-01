#!/bin/bash

# Script to convert relative paths in a .f file to absolute paths
# Usage: ./convert_to_absolute_path.sh <input_file>
# Output: Creates <input_file_basename>_temp.f with absolute paths

# Check if input file is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <input_file>"
    echo "Example: $0 ./backend/target.f"
    exit 1
fi

INPUT_FILE="$1"

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: File '$INPUT_FILE' not found"
    exit 1
fi

# Get the directory and basename of input file
INPUT_DIR=$(dirname "$INPUT_FILE")
INPUT_BASENAME=$(basename "$INPUT_FILE" .f)

# Output file path
OUTPUT_FILE="${INPUT_DIR}/${INPUT_BASENAME}_temp.f"

# Get current working directory (workspace path)
WORKSPACE=$(pwd)

# Process the file
echo "Converting relative paths to absolute paths..."
echo "Input file: $INPUT_FILE"
echo "Output file: $OUTPUT_FILE"
echo "Workspace: $WORKSPACE"

# Read input file line by line and convert relative paths to absolute
while IFS= read -r line || [ -n "$line" ]; do
    # Skip empty lines and comments
    if [[ -z "$line" ]] || [[ "$line" =~ ^[[:space:]]*# ]]; then
        echo "$line"
    # Check if line starts with / (already absolute path)
    elif [[ "$line" =~ ^[[:space:]]*/.*$ ]]; then
        echo "$line"
    # Check if line contains a path (has .v, .sv, or other extensions)
    elif [[ "$line" =~ \.(v|sv|vh|svh)([[:space:]]|$) ]]; then
        # Remove leading/trailing whitespace
        trimmed_line=$(echo "$line" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
        # Convert to absolute path
        echo "${WORKSPACE}/${trimmed_line}"
    else
        echo "$line"
    fi
done < "$INPUT_FILE" > "$OUTPUT_FILE"

echo "Conversion completed successfully!"
echo "Output saved to: $OUTPUT_FILE"

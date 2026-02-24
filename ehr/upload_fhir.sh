#!/bin/bash

PORT=8001
SERVER_URL="http://localhost:$PORT/fhir"

# Check if a directory argument was provided
TARGET_DIR=$1

if [ -z "$TARGET_DIR" ]; then
    echo "Usage: $0 <path_to_fhir_data>"
    echo "Example: $0 ./output/fhir"
    exit 1
fi

# Check if the directory actually exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Directory '$TARGET_DIR' not found."
    exit 1
fi

echo "Connecting to FHIR server at: $SERVER_URL"
echo "------------------------------------------------"

# Phase 1: Uploading Infrastructure (Hospitals & Practitioners)
echo "--- Phase 1: Uploading Infrastructure ---"
for file in "$TARGET_DIR"/*Information*.json; do
  [ -e "$file" ] || continue 

  echo "Uploading infrastructure: $(basename "$file")..."
  curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/fhir+json" \
       --data-binary "@$file" \
       "$SERVER_URL"
  echo " (Done)"
done

echo ""

# Phase 2: Uploading Patients
echo "--- Phase 2: Uploading Patients ---"
for file in "$TARGET_DIR"/*.json; do
  # Skip the files we already uploaded in Phase 1
  if [[ "$file" == *"Information"* ]]; then
    continue
  fi

  echo "Uploading patient: $(basename "$file")..."
  curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/fhir+json" \
       --data-binary "@$file" \
       "$SERVER_URL"
  echo " (Done)"
done

echo "------------------------------------------------"
echo "Upload process complete."

#!/bin/bash
set -e

# This script archives a chat log and ingests it into MISO's memory.

LOG_FILE=$1
ARCHIVE_DIR="dev_archive"
COLLECTION_NAME="miso_development_logs"

# 1. Validate that a log file was provided.
if [ -z "$LOG_FILE" ]; then
  echo "❌ Error: Please provide the path to a chat log file."
  echo "Usage: ./archive_and_analyze.sh <path_to_log.txt>"
  exit 1
fi

# 2. Create the archive directory if it doesn't exist.
echo "📂 Ensuring archive directory '$ARCHIVE_DIR' exists..."
mkdir -p "$ARCHIVE_DIR"

# 3. Copy the log file to the archive.
echo "📋 Copying '$LOG_FILE' to '$ARCHIVE_DIR'..."
cp "$LOG_FILE" "$ARCHIVE_DIR/"

# 4. Ingest the log file into the dedicated ChromaDB collection.
echo "🧠 Ingesting '$LOG_FILE' into the '$COLLECTION_NAME' collection..."
curl -X POST \
  -F "file=@${LOG_FILE}" \
  -F "collection_name=${COLLECTION_NAME}" \
  http://localhost:8888/ingest | python3 -m json.tool

echo "✅ Archival and analysis complete."
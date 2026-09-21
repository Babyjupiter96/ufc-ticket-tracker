#!/bin/bash
# Runs one full poll cycle: fetch latest prices, then re-export the dashboard JSON.
cd "$(dirname "$0")"
python3 fetch_events.py >> poll.log 2>&1
python3 export_json.py >> poll.log 2>&1

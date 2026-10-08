#!/bin/bash
# Serve this folder on http://localhost:8000 and open the isochrone page.
cd "$(dirname "$0")"
(sleep 1; open "http://localhost:8000/index.html") &
echo "Serving on http://localhost:8000 — close this window (or press Ctrl+C) to stop."
python3 -m http.server 8000

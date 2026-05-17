#!/bin/bash
# bilibili-dl — Bilibili video URL extractor + downloader
set -euo pipefail

UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
API="https://api.bilibili.com"
DOWNLOAD=false
QUALITY=80
OUTDIR="."

usage() {
    cat <<EOF
Usage: $0 [-d] [-q 16|32|64|80] [-o DIR] <url>

  -d        Download video (default: show URLs only)
  -q QUAL   Quality: 16=360p, 32=480p, 64=720p, 80=1080p (default: 80)
  -o DIR    Output directory (default: .)
EOF
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in -d) DOWNLOAD=true;; -q) QUALITY="$2"; shift;; -o) OUTDIR="$2"; shift;; -h|--help) usage;; *) URL="$1";;
    esac
    shift
done
[[ -z "${URL:-}" ]] && usage
mkdir -p "$OUTDIR"

# Step 1: BV ID
FINAL_URL=$(curl -sI -L -o /dev/null -w '%{url_effective}' -H "User-Agent: $UA" "$URL")
BVID=$(echo "$FINAL_URL" | grep -oP 'BV[a-zA-Z0-9]{10}')
[[ -z "$BVID" ]] && { echo "ERROR: no BV in $URL"; exit 1; }

# Step 2: video info
INFO=$(curl -s "$API/x/web-interface/view?bvid=$BVID" -H "Referer: https://www.bilibili.com" -H "User-Agent: $UA")
CID=$(echo "$INFO" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['cid'])")
TITLE=$(echo "$INFO" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['title'])")
DUR=$(python3 -c "d=$(echo "$INFO" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['duration'])"); print(f'{d//60}:{d%60:02d}')")
echo "🎬 $TITLE  ⏱ $DUR"

# Step 3: play URLs
PLAY=$(curl -s "$API/x/player/playurl?bvid=$BVID&cid=$CID&qn=$QUALITY&fnval=1&fourk=1" -H "Referer: https://www.bilibili.com" -H "User-Agent: $UA")
QNAME=$(echo "$PLAY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['format'])")
SIZE=$(echo "$PLAY" | python3 "import sys,json; print(json.load(sys.stdin)['data']['durl'][0]['size'])")
echo "📐 $QNAME  📦 $((SIZE/1024/1024)) MB"

if [ "$DOWNLOAD" = false ]; then
    echo "$PLAY" | python3 -c "
import sys, json
d = json.load(sys.stdin)['data']['durl'][0]
print('PRIMARY:'); print(d['url']); print()
print('BACKUPS:'); [print(f'[{i}] {b}') for i,b in enumerate(d['backup_url'])]
"
else
    FNAME=$(echo "$TITLE" | tr '/' '_' | tr -d '\\:*?"<>|')
    OUTFILE="$OUTDIR/${FNAME}.mp4"
    URL=$(echo "$PLAY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['durl'][0]['url'])")
    curl -L -o "$OUTFILE" -H "User-Agent: $UA" -H "Referer: https://www.bilibili.com" --progress-bar "$URL" || {
        URL=$(echo "$PLAY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['durl'][0]['backup_url'][0])")
        curl -L -o "$OUTFILE" -H "User-Agent: $UA" -H "Referer: https://www.bilibili.com" --progress-bar "$URL"
    }
    echo "✅ $OUTFILE ($(du -h "$OUTFILE" | cut -f1))"
fi

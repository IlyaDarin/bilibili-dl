# bilibili-dl

Download or get direct MP4 URLs from Bilibili (b23.tv or BV links).

## Usage

```bash
./bilibili_dl.sh "https://b23.tv/xxxxx"       # show URLs
./bilibili_dl.sh -d "https://b23.tv/xxxxx"    # download (best quality)
./bilibili_dl.sh -d -q 64 "https://b23.tv/xxxxx"  # download 720p
```

Quality: `16`=360p, `32`=480p, `64`=720p, `80`=1080p

## How it works

1. Resolve BV ID from short link
2. Bilibili API → `cid` + metadata
3. Bilibili CDN API → signed MP4 URLs (primary + backup)

## Requirements

- bash
- curl
- python3

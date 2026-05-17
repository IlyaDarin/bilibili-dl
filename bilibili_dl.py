"""
bilibili_dl.py — Bilibili video downloader core (Python, no GUI)
Works on Windows / Linux / macOS.
"""
import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.parse

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
API = "https://api.bilibili.com"
QUALITY_MAP = {"360p": 16, "480p": 32, "720p": 64, "1080p": 80}


def _get(url: str) -> str:
    req = urllib.request.Request(url)
    req.add_header("User-Agent", UA)
    req.add_header("Referer", "https://www.bilibili.com")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def get_bvid(url: str) -> str:
    """Extract BV ID from any Bilibili URL."""
    m = re.search(r"BV[a-zA-Z0-9]{10}", url)
    if m:
        return m.group(0)
    # Follow short link
    req = urllib.request.Request(url, method="HEAD")
    req.add_header("User-Agent", UA)
    with urllib.request.urlopen(req, timeout=15) as r:
        final = r.geturl()
    m = re.search(r"BV[a-zA-Z0-9]{10}", final)
    if m:
        return m.group(0)
    raise ValueError(f"Cannot find BV ID in {url}")


def get_metadata(bvid: str) -> dict:
    """Return {cid, title, duration}."""
    data = json.loads(_get(f"{API}/x/web-interface/view?bvid={bvid}"))
    if data["code"] != 0:
        raise ValueError(f"API error: {data['message']}")
    d = data["data"]
    return {
        "cid": d["cid"],
        "title": d["title"],
        "duration": d["duration"],  # seconds
        "pic": d.get("pic", ""),
    }


def get_playurl(bvid: str, cid: int, quality: int = 80) -> dict:
    """Return {primary_url, backup_urls, fmt, actual_quality, size_bytes}."""
    url = f"{API}/x/player/playurl?bvid={bvid}&cid={cid}&qn={quality}&fnval=1&fourk=1"
    data = json.loads(_get(url))
    if data["code"] != 0:
        raise ValueError(f"Playurl error: {data['message']}")
    d = data["data"]["durl"][0]
    return {
        "primary_url": d["url"],
        "backup_urls": d.get("backup_url", []),
        "fmt": data["data"]["format"],
        "actual_quality": data["data"]["quality"],
        "size_bytes": d["size"],
    }


def download_file(url: str, dest: str, progress_cb=None) -> None:
    """Download URL to dest. progress_cb(bytes_downloaded, total_bytes)."""
    req = urllib.request.Request(url)
    req.add_header("User-Agent", UA)
    req.add_header("Referer", "https://www.bilibili.com")

    with urllib.request.urlopen(req, timeout=600) as r:
        total = int(r.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 65536
        with open(dest, "wb") as f:
            while True:
                chunk = r.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if progress_cb:
                    progress_cb(downloaded, total)
    if progress_cb:
        progress_cb(downloaded, total)  # 100%


def quality_name(q: int) -> str:
    inv = {v: k for k, v in QUALITY_MAP.items()}
    return inv.get(q, f"{q}p")


if __name__ == "__main__":
    # CLI mode — use like bash script for testing
    url = sys.argv[1] if len(sys.argv) > 1 else input("URL: ")
    q = QUALITY_MAP.get(sys.argv[2] if len(sys.argv) > 2 else "", 80)

    bvid = get_bvid(url)
    meta = get_metadata(bvid)
    print(f"🎬 {meta['title']}  ⏱ {meta['duration']//60}:{meta['duration']%60:02d}")

    play = get_playurl(bvid, meta["cid"], q)
    print(f"📐 {play['fmt']}  📦 {play['size_bytes']//1024//1024} MB")

    if len(sys.argv) <= 3 or sys.argv[3] != "--no-dl":
        out = f"{re.sub(r'[\\\\/:*?\"<>|]', '_', meta['title'])}.mp4"
        print(f"⬇ Downloading to {out}...")
        try:
            download_file(play["primary_url"], out)
        except Exception:
            print("Primary failed, trying backup...")
            url_b = play["backup_urls"][0] if play["backup_urls"] else play["primary_url"]
            download_file(url_b, out)
        print(f"✅ {out}")
    else:
        print(f"PRIMARY:\n{play['primary_url']}")

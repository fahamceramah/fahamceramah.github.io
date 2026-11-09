import json
import re
import os
import subprocess
import concurrent.futures
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def parse_siri(title):
    m = re.search(r'siri\s*(\d+)', title, re.IGNORECASE)
    return int(m.group(1)) if m else None

def clean_short_title(title):
    # Remove date and speaker prefix if present
    # e.g. "10-01-2017 SS. DATO' DR. MAZA: Mukadimah Bulughul Maram (siri 1)" -> "Mukadimah Bulughul Maram"
    t = re.sub(r'^\d{2}-\d{2}-\d{4}\s*', '', title)
    t = re.sub(r'^SS\.?\s*DATO[\',]?\s*DR\.?\s*MAZA:\s*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s*\|\s*Bulughul\s*Maram\s*\(siri\s*\d+\)', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s*\|\s*BM\s*\(siri\s*\d+\)', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s*\(siri\s*\d+\)', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s*\|\s*B\.M\.\s*\(\s*Siri\s*\d+\)', '', t, flags=re.IGNORECASE)
    return t.strip()

def main():
    with open(ROOT_DIR / 'playlist.json', 'r') as f:
        playlist = json.load(f)

    entries = playlist.get('entries', [])
    siri_map = {}
    for e in entries:
        s = parse_siri(e.get('title', ''))
        if s and s <= 100 and s not in siri_map:
            siri_map[s] = e

    print(f"Mapped {len(siri_map)} distinct series from playlist (Siri 1 to 100).")

    out_file = ROOT_DIR / 'data' / 'video_metadata_100.json'
    existing = {}
    if out_file.exists():
        with open(out_file, 'r', encoding='utf-8') as f:
            for item in json.load(f):
                existing[item['siri']] = item

    print(f"Already have metadata for {len(existing)} series.")

    to_fetch = [s for s in range(1, 101) if s not in existing and s in siri_map]
    print(f"Need to fetch metadata for {len(to_fetch)} series.")

    def fetch_one(siri_no):
        entry = siri_map[siri_no]
        vid = entry['id']
        cmd = ['./venv/bin/yt-dlp', '-j', f'https://www.youtube.com/watch?v={vid}']
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            info = json.loads(res.stdout)
            full_t = info.get('title', entry.get('title', ''))
            return {
                'video_id': vid,
                'siri': siri_no,
                'short_title': clean_short_title(full_t),
                'full_title': full_t,
                'description': info.get('description', ''),
                'duration': info.get('duration', entry.get('duration', 5000)),
                'upload_date': info.get('upload_date', '2017'),
                'channel': info.get('channel', 'PROmediaTAJDID'),
                'thumbnail': info.get('thumbnail')
            }
        else:
            print(f"Failed {siri_no} ({vid}): {res.stderr[:80]}")
            return {
                'video_id': vid,
                'siri': siri_no,
                'short_title': clean_short_title(entry.get('title', '')),
                'full_title': entry.get('title', ''),
                'description': '',
                'duration': entry.get('duration', 5000),
                'upload_date': '2017',
                'channel': 'PROmediaTAJDID',
                'thumbnail': None
            }

    if to_fetch:
        print("Starting concurrent metadata fetching (max 8 workers)...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            fetched_results = list(executor.map(fetch_one, to_fetch))

        for r in fetched_results:
            existing[r['siri']] = r

    # Save sorted list
    final_list = [existing[s] for s in sorted(existing.keys()) if s <= 100]
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(final_list, f, indent=2, ensure_ascii=False)

    print(f"✓ Successfully prepared metadata for {len(final_list)} series in {out_file}.")

if __name__ == '__main__':
    main()

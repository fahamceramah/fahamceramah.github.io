import os
import sys
import json
import time
import re
import random
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.services.summary_service import generate_video_summary
from backend.app.database.db import init_db, save_video, get_video_by_id

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0"
]

def parse_siri(title: str):
    m = re.search(r'siri\s*(\d+)', title, re.IGNORECASE)
    return int(m.group(1)) if m else None

def clean_short_title(title: str):
    t = re.sub(r'^\d{2}-\d{2}-\d{4}\s*', '', title)
    t = re.sub(r'^SS\.?\s*(?:Prof\.?\s*|Dato[\',]?\s*)*DR\.?\s*MAZA:\s*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s*\|\s*Bulughul\s*Maram\s*\(siri\s*\d+\)', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s*\|\s*BM\s*\(siri\s*\d+\)', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s*\(siri\s*\d+\)', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s*\|\s*B\.M\.\s*\(\s*Siri\s*\d+\)', '', t, flags=re.IGNORECASE)
    return t.strip(' -:|')

def determine_book_section(title: str, siri: int) -> str:
    tl = title.lower()
    if siri <= 50:
        return "Kitab Thaharah (Bab Air & Bersuci)"
    elif siri <= 85:
        return "Kitab Thaharah (Bab Najis & Wuduk)"
    elif "azan" in tl:
        return "Kitab As-Solat (Bab Azan & Iqamah)"
    elif "masjid" in tl:
        return "Kitab As-Solat (Bab Masjid)"
    elif "eid" in tl or "raya" in tl:
        return "Kitab As-Solat (Solat Hari Raya)"
    elif "jumaat" in tl:
        return "Kitab As-Solat (Solat Jumaat)"
    elif "berjemaah" in tl or "imam" in tl or "saf" in tl:
        return "Kitab As-Solat (Solat Berjemaah & Imam)"
    elif "terawih" in tl or "witir" in tl:
        return "Kitab As-Solat (Solat Sunat & Terawih)"
    elif "musafir" in tl or "jamak" in tl or "qasar" in tl:
        return "Kitab As-Solat (Solat Musafir)"
    elif "syarat solat" in tl or "aurat" in tl:
        return "Kitab As-Solat (Syarat-Syarat Solat)"
    else:
        return "Kitab As-Solat (Sifat Solat Nabi)"

def extract_date(title: str, fallback: str = "20240905") -> str:
    m = re.match(r'^(\d{2})-(\d{2})-(\d{4})', title.strip())
    if m:
        return f"{m.group(3)}{m.group(2)}{m.group(1)}"
    return fallback

def fetch_youtube_metadata_humanlike(vid: str, entry_fallback: dict) -> dict:
    ua = random.choice(USER_AGENTS)
    cmd = [
        str(ROOT_DIR / 'venv' / 'bin' / 'yt-dlp'),
        '-j',
        '--skip-download',
        '--no-warnings',
        '--user-agent', ua,
        '--add-header', 'Accept-Language: ms-MY,ms;q=0.9,en-US;q=0.8,en;q=0.7',
        '--socket-timeout', '25',
        f'https://www.youtube.com/watch?v={vid}'
    ]

    for attempt in range(1, 4):
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
            if res.returncode == 0 and res.stdout.strip():
                info = json.loads(res.stdout)
                return {
                    'video_id': vid,
                    'full_title': info.get('title', entry_fallback.get('title', '')),
                    'description': info.get('description', ''),
                    'duration': info.get('duration', entry_fallback.get('duration', 5000)),
                    'upload_date': info.get('upload_date', '20240905'),
                    'thumbnail': info.get('thumbnail')
                }
            else:
                err_lower = res.stderr.lower()
                if '429' in err_lower or 'rate' in err_lower or 'block' in err_lower:
                    wait_sec = 45 * attempt + random.uniform(5, 15)
                    print(f"  [Notice] YouTube rate limit warning. Cooling down for {wait_sec:.1f}s...")
                    time.sleep(wait_sec)
                else:
                    time.sleep(3 * attempt)
        except subprocess.TimeoutExpired:
            print(f"  [Timeout] Metadata request timed out (attempt {attempt}/3). Retrying...")
            time.sleep(4)
        except Exception as e:
            print(f"  [Notice] Metadata error (attempt {attempt}/3): {e}")
            time.sleep(3)

    print(f"  [Fallback] Using playlist cached info for {vid}")
    return {
        'video_id': vid,
        'full_title': entry_fallback.get('title', ''),
        'description': '',
        'duration': entry_fallback.get('duration', 5000),
        'upload_date': '20240905',
        'thumbnail': None
    }

def update_aggregates():
    summaries_dir = ROOT_DIR / "data" / "summaries"
    items = []
    total_duration = 0
    total_hadith = 0
    total_topics = 0

    for fpath in summaries_dir.glob("*.json"):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                d = json.load(f)
            items.append({
                "video_id": d["video_id"],
                "series_no": d["series_no"],
                "title": d["title"],
                "short_title": d["short_title"],
                "speaker": d["speaker"],
                "series_name": d["series_name"],
                "book_section": d.get("book_section", "Kitab As-Solat (Sifat Solat Nabi)"),
                "youtube_url": d["youtube_url"],
                "duration_sec": d["duration_sec"],
                "date_recorded": d["date_recorded"],
                "summary_short": d["summary"]["short"],
                "key_takeaways": d["summary"]["key_takeaways"],
                "has_transcript": d.get("has_transcript", False)
            })
            total_duration += d.get("duration_sec", 0)
            total_hadith += len(d.get("religious_references", []))
            total_topics += len(d.get("topics", []))
        except Exception:
            pass

    items.sort(key=lambda x: x["series_no"])

    with open(ROOT_DIR / "data" / "videos.json", "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

    stats = {
        "total_videos": len(items),
        "total_duration_hours": round(total_duration / 3600, 1),
        "total_hadith_references": total_hadith,
        "total_topics": total_topics
    }
    with open(ROOT_DIR / "data" / "stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

def run_sanity_check(siri_map):
    print("\n================================================================")
    print(" 🔍 RUNNING QUICK SWEEP SANITY CHECK ACROSS ALL 270 SERIES")
    print("================================================================")
    summaries_dir = ROOT_DIR / "data" / "summaries"

    issues = []
    verified_count = 0

    for siri in range(1, 271):
        if siri not in siri_map:
            issues.append(f"Missing in siri_map: Siri {siri}")
            continue

        vid = siri_map[siri]["id"]
        cached_file = summaries_dir / f"{vid}.json"
        db_rec = get_video_by_id(vid)

        if not cached_file.exists():
            issues.append(f"Missing summary JSON file: Siri {siri} [{vid}]")
            continue

        if not db_rec:
            issues.append(f"Missing DB record: Siri {siri} [{vid}]")
            continue

        try:
            with open(cached_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            summary = data.get("summary", {})
            short_s = summary.get("short", "").strip()
            detailed_s = summary.get("detailed", "").strip()
            takeaways = summary.get("key_takeaways", [])
            topics = data.get("topics", [])

            if not short_s or len(short_s) < 50:
                issues.append(f"Empty or too short summary.short for Siri {siri} [{vid}]")
            if not detailed_s or len(detailed_s) < 100:
                issues.append(f"Empty or too short summary.detailed for Siri {siri} [{vid}]")
            if not takeaways or len(takeaways) == 0:
                issues.append(f"No key takeaways for Siri {siri} [{vid}]")
            if not topics or len(topics) == 0:
                issues.append(f"No topics for Siri {siri} [{vid}]")

            verified_count += 1
        except Exception as e:
            issues.append(f"Error parsing JSON for Siri {siri} [{vid}]: {e}")

    # Check videos.json
    with open(ROOT_DIR / "data" / "videos.json", "r", encoding="utf-8") as f:
        videos = json.load(f)

    if len(videos) != 270:
        issues.append(f"videos.json has {len(videos)} items, expected 270")

    # Check stats.json
    with open(ROOT_DIR / "data" / "stats.json", "r", encoding="utf-8") as f:
        stats = json.load(f)

    if stats.get("total_videos") != 270:
        issues.append(f"stats.json total_videos is {stats.get('total_videos')}, expected 270")

    print(f"Verified series with complete content: {verified_count}/270")
    print(f"Total entries in data/videos.json: {len(videos)}")
    print(f"Total duration in stats: {stats.get('total_duration_hours')} hours")
    print(f"Total hadith references: {stats.get('total_hadith_references')}")
    print(f"Total topics: {stats.get('total_topics')}")

    if issues:
        print("\n❌ SANITY CHECK FOUND ISSUES:")
        for iss in issues:
            print(f"  - {iss}")
        return False
    else:
        print("\n✅ ALL 270 SERIES PASSED SANITY CHECK! ZERO EMPTY CONTENT!")
        return True

def main():
    init_db()

    with open(ROOT_DIR / "playlist.json", "r", encoding="utf-8") as f:
        playlist = json.load(f)

    entries = playlist.get("entries", [])
    siri_map = {}
    for e in entries:
        s = parse_siri(e.get("title", ""))
        if s and 1 <= s <= 270:
            siri_map[s] = e

    summaries_dir = ROOT_DIR / "data" / "summaries"
    summaries_dir.mkdir(parents=True, exist_ok=True)

    print("================================================================")
    print(" FahamCeramah: Final Batch Processing Pipeline (Up to Siri 270)")
    print(" Mimicking Human Interaction with YouTube (Anti-IP-Ban Mode)")
    print("================================================================")
    sys.stdout.flush()

    meta_270_file = ROOT_DIR / "data" / "video_metadata_270.json"
    meta_dict = {}
    if meta_270_file.exists():
        with open(meta_270_file, "r", encoding="utf-8") as f:
            for item in json.load(f):
                meta_dict[item["siri"]] = item
    else:
        meta_200_file = ROOT_DIR / "data" / "video_metadata_200.json"
        if meta_200_file.exists():
            with open(meta_200_file, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    meta_dict[item["siri"]] = item

    completed_count = 0
    for s in range(1, 271):
        if s in siri_map:
            vid = siri_map[s]["id"]
            if (summaries_dir / f"{vid}.json").exists() and get_video_by_id(vid):
                completed_count += 1

    print(f"Total series in target range (1..270): {len([s for s in range(1, 271) if s in siri_map])}")
    print(f"Already completed: {completed_count}/270 series.")
    sys.stdout.flush()

    processed_in_session = 0

    for siri in range(201, 271):
        if siri not in siri_map:
            print(f"[Warning] Siri {siri} not found in playlist entries.")
            continue

        entry = siri_map[siri]
        vid = entry["id"]
        cached_file = summaries_dir / f"{vid}.json"
        existing_db = get_video_by_id(vid)

        if cached_file.exists() and existing_db:
            continue

        print(f"\n----------------------------------------------------------------")
        print(f"[{siri}/270] Processing Siri {siri}: [{vid}] {entry.get('title')}")
        sys.stdout.flush()

        # Step 1: Human-mimicking metadata retrieval from YouTube
        if siri in meta_dict and meta_dict[siri].get("description"):
            video_info = meta_dict[siri]
            print(f"  [Cache] Reusing cached metadata for Siri {siri}")
        else:
            human_jitter = random.uniform(4.0, 7.5)
            print(f"  [Human Pause] Browsing delay {human_jitter:.2f}s...")
            time.sleep(human_jitter)

            video_info = fetch_youtube_metadata_humanlike(vid, entry)
            video_info["siri"] = siri
            video_info["short_title"] = clean_short_title(video_info["full_title"])
            meta_dict[siri] = video_info

            sorted_meta = [meta_dict[k] for k in sorted(meta_dict.keys())]
            with open(meta_270_file, "w", encoding="utf-8") as mf:
                json.dump(sorted_meta, mf, indent=2, ensure_ascii=False)

        full_title = video_info.get("full_title", entry.get("title", ""))
        short_title = video_info.get("short_title") or clean_short_title(full_title)
        book_section = determine_book_section(full_title, siri)
        date_rec = extract_date(full_title, video_info.get("upload_date", "20240905"))

        # Step 2: AI Summarization with Gemini
        meta_for_summary = {
            "video_id": vid,
            "siri": siri,
            "short_title": short_title,
            "full_title": full_title,
            "description": video_info.get("description", ""),
            "duration": video_info.get("duration", 4800),
            "upload_date": date_rec
        }

        summary_data = None
        max_attempts = 4
        for attempt in range(1, max_attempts + 1):
            try:
                summary_data = generate_video_summary(meta_for_summary)
                break
            except Exception as e:
                print(f"  [Attempt {attempt}/{max_attempts} Error] {e}")
                if attempt < max_attempts:
                    retry_wait = attempt * 8 + random.uniform(2, 6)
                    print(f"  Waiting {retry_wait:.1f}s before retry...")
                    time.sleep(retry_wait)
                else:
                    print(f"  Failed Siri {siri} after {max_attempts} attempts. Skipping to next.")

        if not summary_data:
            continue

        # Step 3: Record structuring and DB persistence
        record = {
            "video_id": vid,
            "series_no": siri,
            "title": full_title,
            "short_title": short_title,
            "speaker": "SS Dato' Dr. Mohd Asri Zainul Abidin (Dr. MAZA)",
            "series_name": "Bulughul Maram",
            "book_section": book_section,
            "youtube_url": f"https://www.youtube.com/watch?v={vid}",
            "duration_sec": video_info.get("duration", 4800),
            "date_recorded": date_rec,
            "summary": summary_data["summary"],
            "topics": summary_data["topics"],
            "religious_references": summary_data["religious_references"],
            "terminology": summary_data["terminology"],
            "faq": []
        }

        save_video(record)
        with open(cached_file, "w", encoding="utf-8") as out_f:
            json.dump(record, out_f, indent=2, ensure_ascii=False)

        print(f"  ✓ Saved Siri {siri} [{vid}]: {len(record['topics'])} topics, {len(record['religious_references'])} references, {len(record['terminology'])} terms")
        sys.stdout.flush()

        update_aggregates()
        processed_in_session += 1

        post_delay = random.uniform(3.0, 6.0)
        time.sleep(post_delay)

        if processed_in_session % 14 == 0:
            break_time = random.uniform(25.0, 40.0)
            print(f"\n>>> [Natural Human Reading Break] Taking a {break_time:.1f}s pause after {processed_in_session} videos...\n")
            sys.stdout.flush()
            time.sleep(break_time)

    update_aggregates()
    print("\n================================================================")
    print(" ✓ BATCH PROCESSING COMPLETED UP TO VIDEO 270!")
    print("================================================================")
    sys.stdout.flush()

    # Step 4: Run Sanity Check Sweep
    success = run_sanity_check(siri_map)
    if not success:
        print("\n❌ Sweep check failed with issues!")
        sys.exit(1)
    else:
        print("\n🎉 Sweep check successful! Ready for commit and push.")

if __name__ == "__main__":
    main()

import os
import sys
import json
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.services.summary_service import generate_video_summary
from backend.app.database.db import init_db, save_video, get_video_by_id

def main():
    init_db()

    meta_file = ROOT_DIR / "data" / "video_metadata_100.json"
    if not meta_file.exists():
        print("Error: data/video_metadata_100.json not found yet.")
        return

    with open(meta_file, "r", encoding="utf-8") as f:
        videos = json.load(f)

    summaries_dir = ROOT_DIR / "data" / "summaries"
    summaries_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loaded {len(videos)} series from metadata file.")

    completed_count = 0
    for v in videos:
        vid = v["video_id"]
        siri = v["siri"]
        cached_file = summaries_dir / f"{vid}.json"
        existing_db = get_video_by_id(vid)

        if cached_file.exists() and existing_db:
            completed_count += 1

    print(f"Already completed: {completed_count}/100 series. Starting remaining...")

    for v in videos:
        vid = v["video_id"]
        siri = v["siri"]
        title = v.get("short_title", v.get("full_title", ""))

        cached_file = summaries_dir / f"{vid}.json"
        existing_db = get_video_by_id(vid)

        if cached_file.exists() and existing_db:
            continue

        print(f"\n[{siri}/100] Processing Siri {siri}: [{vid}] {title}")

        summary_data = None
        max_attempts = 4
        for attempt in range(1, max_attempts + 1):
            try:
                summary_data = generate_video_summary(v)
                break
            except Exception as e:
                print(f"Attempt {attempt}/{max_attempts} failed for Siri {siri}: {e}")
                if attempt < max_attempts:
                    sleep_time = attempt * 5
                    print(f"Waiting {sleep_time}s before retrying...")
                    time.sleep(sleep_time)
                else:
                    print(f"Failed to process Siri {siri} after {max_attempts} attempts. Moving to next.")

        if not summary_data:
            continue

        record = {
            "video_id": vid,
            "series_no": siri,
            "title": v.get("full_title", title),
            "short_title": title,
            "speaker": "SS Dato' Dr. Mohd Asri Zainul Abidin (Dr. MAZA)",
            "series_name": "Bulughul Maram",
            "book_section": "Kitab Thaharah / Kitab Ahkam",
            "youtube_url": f"https://www.youtube.com/watch?v={vid}",
            "duration_sec": v.get("duration", 4800),
            "date_recorded": v.get("upload_date", "2017"),
            "summary": summary_data["summary"],
            "topics": summary_data["topics"],
            "religious_references": summary_data["religious_references"],
            "terminology": summary_data["terminology"],
            "faq": []  # Not needed as requested by user
        }

        # Save to DB & JSON backup
        save_video(record)
        with open(cached_file, "w", encoding="utf-8") as out_f:
            json.dump(record, out_f, indent=2, ensure_ascii=False)

        print(f"✓ Saved Siri {siri} [{vid}]: {len(record['topics'])} topics, {len(record['religious_references'])} references")

        # Rate-limit friendly pause (1.5 seconds)
        time.sleep(1.5)

    print("\n✓ PROCESSING COMPLETE UP TO SIRI 100!")

if __name__ == "__main__":
    main()

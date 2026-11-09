import os
import sys
import json
import time
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.services.summary_service import generate_video_summary
from backend.app.database.db import init_db, save_video, get_video_by_id

def parse_vtt(vtt_path):
    if not os.path.exists(vtt_path):
        return None, None

    with open(vtt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    import re
    time_re = re.compile(r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})')
    tag_re = re.compile(r'<[^>]+>')

    segments = []
    lines = content.splitlines()
    curr_time = None
    curr_text = []
    seen = set()

    for line in lines:
        line = line.strip()
        m = time_re.search(line)
        if m:
            if curr_time and curr_text:
                txt = " ".join(curr_text).strip()
                if txt and txt not in seen:
                    segments.append({"start": curr_time[0], "end": curr_time[1], "text": txt})
                    seen.add(txt)
            curr_time = (m.group(1), m.group(2))
            curr_text = []
        elif curr_time:
            clean = tag_re.sub('', line).strip()
            if clean and not clean.startswith('NOTE') and not clean.startswith('WEBVTT') and 'align:' not in clean:
                if not curr_text or clean != curr_text[-1]:
                    curr_text.append(clean)

    if curr_time and curr_text:
        txt = " ".join(curr_text).strip()
        if txt and txt not in seen:
            segments.append({"start": curr_time[0], "end": curr_time[1], "text": txt})

    full_text = " ".join([s["text"] for s in segments])
    return full_text, segments

def main():
    init_db()

    meta_file = ROOT_DIR / "data" / "video_metadata.json"
    if not meta_file.exists():
        print("Error: data/video_metadata.json not found.")
        return

    with open(meta_file, "r", encoding="utf-8") as f:
        videos = json.load(f)

    summaries_dir = ROOT_DIR / "data" / "summaries"
    summaries_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting processing for {len(videos)} videos...")

    for v in videos:
        vid = v["video_id"]
        siri = v["siri"]
        title = v["short_title"]
        print(f"\n==================================================")
        print(f"Processing Siri {siri}: [{vid}] {title}")

        # Check if already processed
        cached_file = summaries_dir / f"{vid}.json"
        existing_db = get_video_by_id(vid)

        vtt_file = ROOT_DIR / "data" / "transcripts" / f"auto_{vid}.ms.vtt"
        full_transcript, segments = parse_vtt(vtt_file)

        if cached_file.exists() and existing_db:
            print(f"✓ Already processed and saved in DB: Siri {siri}")
            continue

        transcript_sample = full_transcript[:15000] if full_transcript else ""

        print(f"Generating comprehensive summary with Gemini 3.5 Flash...")
        try:
            summary_data = generate_video_summary(v, transcript_sample)
        except Exception as e:
            print(f"Error generating summary with Gemini: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)
            summary_data = generate_video_summary(v, transcript_sample)

        # Merge with base video metadata
        record = {
            "video_id": vid,
            "series_no": siri,
            "title": v.get("full_title", title),
            "short_title": title,
            "speaker": "SS Dato' Dr. Mohd Asri Zainul Abidin (Dr. MAZA)",
            "series_name": "Bulughul Maram",
            "book_section": "Kitab Thaharah (Bab Air & Bersuci)",
            "youtube_url": f"https://www.youtube.com/watch?v={vid}",
            "duration_sec": v.get("duration", 4800),
            "date_recorded": v.get("upload_date", "2017"),
            "summary": summary_data["summary"],
            "topics": summary_data["topics"],
            "religious_references": summary_data["religious_references"],
            "terminology": summary_data["terminology"],
            "faq": summary_data["faq"],
        }

        # Save to DB
        save_video(record, full_transcript, segments)

        # Save to JSON backup
        with open(cached_file, "w", encoding="utf-8") as out_f:
            json.dump(record, out_f, indent=2, ensure_ascii=False)

        print(f"✓ Saved Siri {siri} successfully: {len(record['topics'])} topics, {len(record['religious_references'])} references, {len(record['faq'])} FAQs")

        # Small pause between calls to avoid hitting rate limits
        time.sleep(2)

    print("\n✓ ALL 10 VIDEOS PROCESSED AND SAVED SUCCESSFULLY!")

if __name__ == "__main__":
    main()

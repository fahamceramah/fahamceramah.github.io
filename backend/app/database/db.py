import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Dict, Any

DB_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "database"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "fahamceramah.db"

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS videos (
        video_id TEXT PRIMARY KEY,
        series_no INTEGER NOT NULL,
        title TEXT NOT NULL,
        short_title TEXT NOT NULL,
        speaker TEXT NOT NULL,
        series_name TEXT NOT NULL,
        book_section TEXT NOT NULL,
        youtube_url TEXT NOT NULL,
        duration_sec INTEGER NOT NULL,
        date_recorded TEXT NOT NULL,
        summary_short TEXT NOT NULL,
        summary_detailed TEXT NOT NULL,
        key_takeaways_json TEXT NOT NULL,
        topics_json TEXT NOT NULL,
        references_json TEXT NOT NULL,
        terminology_json TEXT NOT NULL,
        faq_json TEXT NOT NULL,
        transcript_text TEXT,
        transcript_segments_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Drop old FTS if needed and recreate standalone FTS5
    cursor.execute("DROP TABLE IF EXISTS videos_fts;")
    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS videos_fts USING fts5(
        video_id UNINDEXED,
        title,
        short_title,
        summary_short,
        summary_detailed,
        topics_text
    );
    """)

    conn.commit()
    conn.close()

def save_video(video_data: Dict[str, Any], transcript_text: Optional[str] = None, transcript_segments: Optional[List[Dict[str, Any]]] = None):
    conn = get_connection()
    cursor = conn.cursor()

    # Extract plain topics text for FTS
    topics = video_data.get("topics", [])
    topics_text = " ".join([f"{t.get('title', '')} {t.get('summary', '')}" for t in topics])

    cursor.execute("""
    INSERT OR REPLACE INTO videos (
        video_id, series_no, title, short_title, speaker, series_name, book_section,
        youtube_url, duration_sec, date_recorded, summary_short, summary_detailed,
        key_takeaways_json, topics_json, references_json, terminology_json, faq_json,
        transcript_text, transcript_segments_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        video_data["video_id"],
        video_data["series_no"],
        video_data["title"],
        video_data["short_title"],
        video_data.get("speaker", "SS Dato' Dr. Mohd Asri Zainul Abidin (Dr. MAZA)"),
        video_data.get("series_name", "Bulughul Maram"),
        video_data.get("book_section", "Kitab Thaharah (Bab Air & Bersuci)"),
        video_data["youtube_url"],
        video_data["duration_sec"],
        video_data["date_recorded"],
        video_data["summary"]["short"],
        video_data["summary"]["detailed"],
        json.dumps(video_data["summary"].get("key_takeaways", []), ensure_ascii=False),
        json.dumps(video_data.get("topics", []), ensure_ascii=False),
        json.dumps(video_data.get("religious_references", []), ensure_ascii=False),
        json.dumps(video_data.get("terminology", []), ensure_ascii=False),
        json.dumps(video_data.get("faq", []), ensure_ascii=False),
        transcript_text,
        json.dumps(transcript_segments, ensure_ascii=False) if transcript_segments else None
    ))

    # Re-sync standalone FTS table
    cursor.execute("DELETE FROM videos_fts WHERE video_id = ?", (video_data["video_id"],))
    cursor.execute("""
    INSERT INTO videos_fts (video_id, title, short_title, summary_short, summary_detailed, topics_text)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        video_data["video_id"],
        video_data["title"],
        video_data["short_title"],
        video_data["summary"]["short"],
        video_data["summary"]["detailed"],
        topics_text
    ))

    conn.commit()
    conn.close()

def get_all_videos() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT video_id, series_no, title, short_title, speaker, series_name, book_section,
           youtube_url, duration_sec, date_recorded, summary_short,
           key_takeaways_json, (transcript_text IS NOT NULL) AS has_transcript
    FROM videos
    ORDER BY series_no ASC
    """)
    rows = cursor.fetchall()
    results = []
    for r in rows:
        results.append({
            "video_id": r["video_id"],
            "series_no": r["series_no"],
            "title": r["title"],
            "short_title": r["short_title"],
            "speaker": r["speaker"],
            "series_name": r["series_name"],
            "book_section": r["book_section"],
            "youtube_url": r["youtube_url"],
            "duration_sec": r["duration_sec"],
            "date_recorded": r["date_recorded"],
            "summary_short": r["summary_short"],
            "key_takeaways": json.loads(r["key_takeaways_json"]) if r["key_takeaways_json"] else [],
            "has_transcript": bool(r["has_transcript"])
        })
    conn.close()
    return results

def get_video_by_id(video_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM videos WHERE video_id = ?
    """, (video_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    data = {
        "video_id": row["video_id"],
        "series_no": row["series_no"],
        "title": row["title"],
        "short_title": row["short_title"],
        "speaker": row["speaker"],
        "series_name": row["series_name"],
        "book_section": row["book_section"],
        "youtube_url": row["youtube_url"],
        "duration_sec": row["duration_sec"],
        "date_recorded": row["date_recorded"],
        "summary": {
            "short": row["summary_short"],
            "detailed": row["summary_detailed"],
            "key_takeaways": json.loads(row["key_takeaways_json"]) if row["key_takeaways_json"] else []
        },
        "topics": json.loads(row["topics_json"]) if row["topics_json"] else [],
        "religious_references": json.loads(row["references_json"]) if row["references_json"] else [],
        "terminology": json.loads(row["terminology_json"]) if row["terminology_json"] else [],
        "faq": json.loads(row["faq_json"]) if row["faq_json"] else [],
        "has_full_transcript": bool(row["transcript_text"]),
        "transcript_text": row["transcript_text"],
        "transcript_segments": json.loads(row["transcript_segments_json"]) if row["transcript_segments_json"] else []
    }
    conn.close()
    return data

def search_videos(query: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        SELECT v.video_id, v.series_no, v.title, v.short_title, v.summary_short, v.duration_sec
        FROM videos_fts f
        JOIN videos v ON f.video_id = v.video_id
        WHERE videos_fts MATCH ?
        ORDER BY rank
        LIMIT 20
        """, (query,))
        rows = cursor.fetchall()
        results = [dict(r) for r in rows]
    except sqlite3.OperationalError:
        cursor.execute("""
        SELECT video_id, series_no, title, short_title, summary_short, duration_sec
        FROM videos
        WHERE title LIKE ? OR summary_short LIKE ? OR summary_detailed LIKE ?
        ORDER BY series_no ASC
        LIMIT 20
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))
        rows = cursor.fetchall()
        results = [dict(r) for r in rows]
    conn.close()
    return results

import os
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import config
from backend.app.database.db import get_all_videos, get_video_by_id, search_videos, get_connection

BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="FahamCeramah API",
    description="Accessible Malay Religious Lecture Summarizer & Knowledge Library",
    version=config.app_version
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Endpoints
@app.get("/api/videos")
def list_videos():
    videos = get_all_videos()
    return {"status": "success", "count": len(videos), "videos": videos}

@app.get("/api/videos/{video_id}")
def video_detail(video_id: str):
    video = get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Ceramah video not found")
    return {"status": "success", "video": video}

@app.get("/api/videos/{video_id}/export/markdown", response_class=PlainTextResponse)
def export_markdown(video_id: str):
    video = get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Ceramah video not found")

    md = f"""# {video['title']}
**Siri:** {video['series_no']} | **Penceramah:** {video['speaker']}
**Kitab:** {video['series_name']} - {video['book_section']}
**Pautan YouTube:** {video['youtube_url']}
**Tarikh Kuliah:** {video['date_recorded']} | **Durasi:** {video['duration_sec'] // 60} minit

---

## 1. Ringkasan Pantas
{video['summary']['short']}

### Pengajaran & Amalan Utama
"""
    for point in video['summary']['key_takeaways']:
        md += f"- {point}\n"

    md += f"""
---

## 2. Huraian Terperinci
{video['summary']['detailed']}

---

## 3. Dalil & Rujukan Agama
"""
    for ref in video.get('religious_references', []):
        md += f"### {ref['reference']} ({ref.get('grade', 'Sahih')})\n"
        if ref.get('narrator'):
            md += f"**Perawi:** {ref['narrator']} | **Sumber:** {ref.get('source_book', '')}\n\n"
        if ref.get('text_ar'):
            md += f"> **Matan Arab:**\n> {ref['text_ar']}\n\n"
        if ref.get('text_ms'):
            md += f"**Terjemahan:** {ref['text_ms']}\n\n"

    md += """
---

## 4. Topik Perbincangan & Cap Masa
| Masa | Topik | Huraian Ringkas |
|---|---|---|
"""
    for t in video.get('topics', []):
        md += f"| {t['timestamp']} | {t['title']} | {t['summary']} |\n"

    md += """
---

## 5. Glosari Istilah
"""
    for term in video.get('terminology', []):
        md += f"- **{term['term']}** *({term['category']})*: {term['explanation']}\n"

    md += """
---

## Penafian & Penghargaan
Semua rakaman video kuliah asal yang diringkaskan di sini adalah hasil usaha gigih dan dedikasi berterusan pihak **PROmediaTAJDID**, **Pejabat Mufti Negeri Perlis**, dan seluruh barisan pasukan penerbitan yang bertungkus-lumus merakam serta menyiarkan kuliah pengajian ini. FahamCeramah hanya menyediakan ringkasan bertulis semata-mata untuk memudahkan capaian ilmu, rujukan, serta manfaat mereka yang memerlukan.
"""
    return md

@app.get("/api/search")
def search(q: str = Query(..., min_length=2)):
    results = search_videos(q)
    return {"status": "success", "query": q, "count": len(results), "results": results}

@app.get("/api/stats")
def get_stats():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*), SUM(duration_sec) FROM videos")
    row = c.fetchone()
    total_videos = row[0] or 0
    total_seconds = row[1] or 0

    c.execute("SELECT references_json, topics_json FROM videos")
    rows = c.fetchall()
    total_hadith = 0
    total_topics = 0
    for r in rows:
        if r["references_json"]:
            total_hadith += len(json.loads(r["references_json"]))
        if r["topics_json"]:
            total_topics += len(json.loads(r["topics_json"]))
    conn.close()

    return {
        "total_videos": total_videos,
        "total_duration_hours": round(total_seconds / 3600, 1),
        "total_hadith_references": total_hadith,
        "total_topics": total_topics
    }

@app.get("/api/dictionaries/terms")
def get_dictionary_terms():
    dict_path = BASE_DIR / "data" / "dictionaries" / "malay-islamic-terms.json"
    if dict_path.exists():
        with open(dict_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"terms": []}

# Frontend Static Files & Folders (Matches GitHub Pages structure)
if (BASE_DIR / "css").exists():
    app.mount("/css", StaticFiles(directory=str(BASE_DIR / "css")), name="css")
if (BASE_DIR / "js").exists():
    app.mount("/js", StaticFiles(directory=str(BASE_DIR / "js")), name="js")
if (BASE_DIR / "data").exists():
    app.mount("/data", StaticFiles(directory=str(BASE_DIR / "data")), name="data")

@app.get("/")
@app.get("/index.html")
def serve_index():
    return FileResponse(str(BASE_DIR / "index.html"))

@app.get("/ceramah")
@app.get("/ceramah.html")
def serve_ceramah():
    return FileResponse(str(BASE_DIR / "ceramah.html"))

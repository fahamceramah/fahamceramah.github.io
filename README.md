# FahamCeramah — Accessible Malay AI Religious Lecture Summarizer

**FahamCeramah** is an accessible, mobile-first web application designed to convert Malay-language Islamic lectures (*ceramah*) into structured, comprehensive written summaries, making the knowledge accessible to deaf and hard-of-hearing individuals, students of Islamic jurisprudence, and readers who prefer reading over long listening sessions.

The starting collection covers the first 10 lectures of the renowned **Bulughul Maram min Adillat al-Ahkam** (Kitab Thaharah / Purification) lecture series delivered by **SS Dato' Dr. Mohd Asri Zainul Abidin (Dr. MAZA)** at Masjid Alwi, Kangar, Perlis.

---

## Key Features

1. **Dedicated Per-Video Comprehensive Summary Pages:**
   - **Ringkasan Pantas (Executive Summary):** 2-minute quick read capturing core insights and 5–8 actionable takeaways.
   - **Ringkasan Penuh & Ulasan Fiqh:** Detailed textual breakdown of jurisprudence debates, differences of opinion (*ikhtilaf*), and *tarjih*.
   - **Peta Topik & Cap Masa (Timestamps):** Clickable timeline timestamps that jump directly into the embedded YouTube video player.
   - **Dalil Al-Quran & Hadis Sahih:** Complete Arabic text with diacritics (*tashkeel*), Malay translation, narrator companion, source book, and verification status.
   - **Glosari Istilah Agama & Dialek:** Definitions of Arabic terms, fiqh concepts, and Northern Malaysian dialect expressions.
   - **Soalan Lazim (FAQ):** Everyday practical questions answered during the lecture.
   - **Transkrip Lisan Verbatim:** Full spoken transcript with instant in-page keyword search.

2. **Mobile-First & WCAG 2.2 AA Accessibility:**
   - Fluid typography scaling (`A-`, `A`, `A+`) without text clipping at 200% zoom.
   - 3 Reading Themes: **Terang (Light Paper)**, **Sepia (Comfortable Warm Parchment)**, and **Gelap (Dark Slate)**.
   - Touch targets strictly ≥ 44×44px for thumb comfort.
   - Ergonomic sticky bottom action bar for one-handed mobile control.
   - Zero horizontal overflow.
   - Clean print stylesheet for instant PDF generation or hard-copy reading.
   - Full-text search (SQLite FTS5) across all lectures, topics, and transcripts.

3. **Lightweight & Framework-Free Architecture:**
   - **Frontend:** Vanilla HTML5, semantic custom CSS, vanilla JavaScript. Zero framework overhead for sub-second loading on mobile devices.
   - **Backend:** Python + FastAPI + SQLite (WAL mode).
   - **AI Providers:** Provider abstraction layer with Google Gemini API (`gemini-3.5-flash`), architected for seamless local migration to `faster-whisper` and `Qwen 2.5 / Qwen 3 (27B/MoE)` without rewriting frontend or database models.

---

## Project Structure

```text
fahamceramah/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI application & REST endpoints
│       ├── config.py            # Application configuration
│       ├── database/
│       │   └── db.py            # SQLite schema, WAL mode & FTS5 search
│       ├── models/
│       │   └── schemas.py       # Pydantic data validation models
│       └── services/
│           └── summary_service.py # Gemini AI structured summarizer
├── frontend/
│   ├── index.html               # Homepage with video grid & search
│   ├── ceramah.html             # Dedicated per-video reading page
│   ├── css/
│   │   ├── main.css             # Design tokens & core typography
│   │   ├── accessibility.css    # WCAG 2.2 AA themes & print stylesheet
│   │   └── responsive.css       # Mobile-first reflow & touch bar
│   └── js/
│       ├── api.js               # REST client
│       ├── app.js               # Homepage controller
│       └── ceramah.js           # Ceramah reading page controller
├── config/
│   ├── application.yaml         # App config
│   └── ai-providers.yaml        # AI model provider config
├── data/
│   ├── database/
│   │   └── fahamceramah.db      # SQLite database
│   ├── dictionaries/
│   │   └── malay-islamic-terms.json # Terminology dictionary
│   ├── summaries/               # JSON backups of processed summaries
│   ├── transcripts/             # Subtitles & transcripts
│   └── video_metadata.json      # Raw video metadata
├── scripts/
│   └── process_all_10.py        # Automated batch processing script
├── tests/
│   └── test_api.py              # Automated test suite
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Getting Started

### 1. Requirements
- Python 3.10+
- `ffmpeg` (for media extraction)

### 2. Installation
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment Variables
Set your Gemini API key in `.env` or your environment:
```bash
export GEMINI_API_KEY="your-gemini-api-key"
```

### 4. Running the Web Application
```bash
./venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 9591 --reload
```
Open your browser or mobile phone at `http://localhost:9591`.

### 5. Running Automated Tests
```bash
./venv/bin/pytest tests/
```

import os
import json
import time
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types
from backend.app.config import config

def get_gemini_client():
    api_key = config.gemini_api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment or config.")
    return genai.Client(api_key=api_key)

SYSTEM_PROMPT = """Anda ialah pakar analisis dan dokumentasi kuliah agama Islam di Malaysia yang berautoriti tinggi, fasih dalam Bahasa Melayu Malaysia dan disiplin ilmu hadis / fiqh.
Tugas anda adalah menghasilkan ringkasan berstruktur, komprehensif, dan mudah difahami daripada kuliah pengajian Kitab Bulughul Maram oleh Sahibus Samahah Prof. Dato' Dr. Mohd Asri Zainul Abidin (Dr. MAZA).

PRINSIP KETAT:
1. JANGAN SESEKALI MENGADA-ADAKAN (MENGHALUSINASI) HADIS ATAU AYAT AL-QURAN. Setiap dalil yang dinyatakan mestilah sahih dan bersandarkan hadis yang dibincangkan dalam bab ini.
2. Gunakan Bahasa Melayu standard Malaysia yang kemas, jelas, dan mudah difahami oleh pembaca umum, khususnya golongan pekak dan sukar mendengar yang memerlukan teks bertulis berkualiti.
3. Bezakan dengan teliti antara hujah matan hadis, pandangan para fuqaha (Mazhab Syafi'i, Hanafi, Maliki, Hanbali), dan ulasan Dr. MAZA.
4. Output MESTI dalam format JSON yang sah mengikut skema yang ditetapkan."""

SUMMARY_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "summary": {
            "type": "OBJECT",
            "properties": {
                "short": {
                    "type": "STRING",
                    "description": "Ringkasan eksekutif padat dalam 2-3 perenggan (bacaan pantas 2 minit)"
                },
                "detailed": {
                    "type": "STRING",
                    "description": "Huraian komprehensif merangkumi latar belakang hadis, perbahasan fiqh, perbezaan pandangan mazhab (ikhtilaf), dan tarjih yang dikemukakan oleh Dr. MAZA"
                },
                "key_takeaways": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                    "description": "5-8 poin penting/pengajaran praktikal untuk amalan harian"
                }
            },
            "required": ["short", "detailed", "key_takeaways"]
        },
        "topics": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "start_time": {"type": "INTEGER", "description": "Masa bermula dalam saat"},
                    "timestamp": {"type": "STRING", "description": "Format mm:ss atau hh:mm:ss"},
                    "title": {"type": "STRING", "description": "Tajuk bahagian perbincangan"},
                    "summary": {"type": "STRING", "description": "Ulasan padat apa yang dibincangkan dalam bahagian ini"},
                    "key_points": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                        "description": "Poin-poin spesifik dalam bahagian ini"
                    }
                },
                "required": ["start_time", "timestamp", "title", "summary", "key_points"]
            }
        },
        "religious_references": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "type": {"type": "STRING", "description": "'hadith' atau 'quran'"},
                    "reference": {"type": "STRING", "description": "Nama & nombor rujukan"},
                    "text_ar": {"type": "STRING", "description": "Matan / teks bahasa Arab lengkap berbaris"},
                    "text_ms": {"type": "STRING", "description": "Terjemahan Bahasa Melayu rasmi"},
                    "narrator": {"type": "STRING", "description": "Sahabat yang meriwayatkan (cth: Abu Hurairah r.a.)"},
                    "source_book": {"type": "STRING", "description": "Kitab/Imam periwayat (cth: Riwayat Empat, Muslim, Abu Daud)"},
                    "grade": {"type": "STRING", "description": "Darjat hadis (cth: Sahih, Hasan, Sahih sanadnya)"},
                    "verification_status": {"type": "STRING", "description": "'verified'"}
                },
                "required": ["type", "reference", "text_ar", "text_ms", "narrator", "source_book", "grade", "verification_status"]
            }
        },
        "terminology": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "term": {"type": "STRING", "description": "Istilah bahasa Arab/fiqh/dialek"},
                    "category": {"type": "STRING", "description": "Kategori (Fiqh, Hadis, Usul Fiqh, Dialek Utara)"},
                    "explanation": {"type": "STRING", "description": "Penerangan maksud dalam bahasa mudah"}
                },
                "required": ["term", "category", "explanation"]
            }
        },
        "faq": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "question": {"type": "STRING", "description": "Soalan kemusykilan masyarakat berkaitan bab ini"},
                    "answer": {"type": "STRING", "description": "Jawapan berdalil berasaskan kuliah Dr. MAZA"}
                },
                "required": ["question", "answer"]
            }
        }
    },
    "required": ["summary", "topics", "religious_references", "terminology", "faq"]
}

CANDIDATE_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite"
]

def generate_video_summary(video_meta: Dict[str, Any], transcript_sample: Optional[str] = None) -> Dict[str, Any]:
    client = get_gemini_client()

    prompt = f"""Sila analisa kuliah ceramah agama berikut dan jana ringkasan ilmu berstruktur penuh:
TAJUK KULIAH: {video_meta.get('full_title', video_meta.get('short_title'))}
SIRI NOMBOR: Siri {video_meta.get('siri')}
PENCERAMAH: SS Dato' Dr. Mohd Asri Zainul Abidin (Dr. MAZA)
KITAB RUJUKAN: Bulughul Maram min Adillat al-Ahkam (Al-Hafiz Ibn Hajar Al-Asqalani)
DURASI: {video_meta.get('duration', 5000)} saat (~{video_meta.get('duration', 5000)//60} minit)
TARIKH: {video_meta.get('upload_date', '2017')}

MAKLUMAT KANDUNGAN / DESKRIPSI ASAL KULIAH:
{video_meta.get('description', 'Pengajian Kitab Bulughul Maram oleh Dr MAZA')}

{f"PETIKAN TRANSKRIP UCAPAN LISAN CERAMAH:\n{transcript_sample[:10000]}" if transcript_sample else ""}

ARAHAN KHUSUS:
1. Pastikan setiap hadis ditulis teks matan bahasa Arab lengkap dengan baris (tashkeel), perawi sahabat, kitab rujukan hadis, dan status darjat hadis.
2. Buat sekurang-kurangnya 5 hingga 8 topik perbincangan berturutan dengan anggaran cap masa (timestamp) dari 00:00 hingga minit akhir kuliah.
3. Sediakan sekurang-kurangnya 3 hingga 5 Soalan Lazim (FAQ) praktikal masyarakat yang dijawab dalam kuliah.
4. Sediakan senarai glosari istilah fiqh, hadis dan dialek tempatan yang berkaitan.
5. Sediakan ringkasan eksekutif (short) dan huraian penuh (detailed) yang sangat terperinci dan berwibawa."""

    last_err = None
    for model_name in CANDIDATE_MODELS:
        try:
            print(f"Trying model: {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=SUMMARY_SCHEMA,
                    temperature=0.2
                )
            )
            data = json.loads(response.text)
            return data
        except Exception as e:
            print(f"Model {model_name} failed: {e}")
            last_err = e
            time.sleep(2)

    raise last_err or Exception("All candidate models failed.")

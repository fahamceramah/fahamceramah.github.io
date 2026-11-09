from typing import List, Optional
from pydantic import BaseModel, Field

class TopicItem(BaseModel):
    start_time: int = Field(0, description="Start time in seconds")
    timestamp: str = Field("00:00", description="Formatted timestamp mm:ss or hh:mm:ss")
    title: str = Field(..., description="Topic title in Bahasa Melayu")
    summary: str = Field(..., description="Summary of discussion for this topic")
    key_points: List[str] = Field(default_factory=list, description="Key discussion points")

class ReligiousReference(BaseModel):
    type: str = Field("hadith", description="'hadith' or 'quran'")
    reference: str = Field(..., description="Reference title/number (e.g. Hadis No. 1: Bulughul Maram)")
    text_ar: Optional[str] = Field(None, description="Arabic text of the verse or hadith")
    text_ms: Optional[str] = Field(None, description="Malay translation")
    narrator: Optional[str] = Field(None, description="Companion / rawi (e.g. Abu Hurairah r.a.)")
    source_book: Optional[str] = Field(None, description="Mukharrij (e.g. Abu Daud, Tirmizi, Muslim)")
    grade: Optional[str] = Field(None, description="Hadith status: Sahih, Hasan, Dha'if")
    verification_status: str = Field("verified", description="'verified' or 'unverified'")

class TerminologyItem(BaseModel):
    term: str = Field(..., description="Term in Arabic or Malay")
    category: str = Field("Fiqh", description="Category e.g. Fiqh, Usul, Dialek, Gelaran")
    explanation: str = Field(..., description="Clear explanation in simple Bahasa Melayu")

class FAQItem(BaseModel):
    question: str = Field(..., description="Practical question answered in lecture")
    answer: str = Field(..., description="Direct answer derived from Dr. MAZA's explanation")

class SummaryContent(BaseModel):
    short: str = Field(..., description="Executive summary in 2-3 paragraphs or 5-8 bullet points")
    detailed: str = Field(..., description="Comprehensive lecture breakdown and explanation")
    key_takeaways: List[str] = Field(default_factory=list, description="Key actionable lessons and principles")

class CeramahVideo(BaseModel):
    video_id: str
    series_no: int
    title: str
    short_title: str
    speaker: str = "SS Dato' Dr. Mohd Asri Zainul Abidin (Dr. MAZA)"
    series_name: str = "Bulughul Maram"
    book_section: str = "Kitab Thaharah (Bab Air & Bersuci)"
    youtube_url: str
    duration_sec: int
    date_recorded: str
    summary: SummaryContent
    topics: List[TopicItem] = Field(default_factory=list)
    religious_references: List[ReligiousReference] = Field(default_factory=list)
    terminology: List[TerminologyItem] = Field(default_factory=list)
    faq: List[FAQItem] = Field(default_factory=list)
    has_full_transcript: bool = False
    transcript_preview: Optional[str] = None

# Agent TODO: Ceramah Malaysia — Accessible Malay AI Summarizer

**Project objective:** Build an AI-powered application that converts Malay-language religious lectures (ceramah) into easy-to-understand written summaries, making the content accessible to deaf and hard-of-hearing people and people who have difficulty understanding spoken lectures.

The initial content source will be the provided Dr. MAZA YouTube lecture. The long-term goal is to support ceramah from Dr. MAZA and other Malaysian ustaz, across different Malaysian Malay dialects and speaking styles.

I recommend building this as a **Malay-first, provider-independent AI application**, rather than an application tightly coupled to Gemini.

The first release can use your Google AI Pro/Gemini ecosystem, but its architecture should allow you to replace Gemini with local Qwen models without redesigning the application.

## 1. Project vision

### Primary users

1. Deaf and hard-of-hearing individuals.
2. People who have difficulty following spoken Malay.
3. People who prefer reading rather than listening to lengthy ceramah.
4. People who want to revisit important religious discussions.
5. People who want searchable knowledge extracted from Malaysian religious lectures.

### Core experience

A user opens the application, selects a ceramah video, and receives:

- Full Malay transcript.
- Short summary.
- Detailed summary.
- Main topics discussed.
- Important points and arguments.
- Quranic verses and hadith mentioned, where identifiable.
- Important names, references and terminology.
- Timestamped sections.
- Frequently asked questions (FAQ).
- Malay vocabulary explanations for difficult religious terminology.

**Important principle:** This application is an accessibility and knowledge-preservation tool, not an Islamic fatwa generator. It must distinguish what Dr. MAZA actually says from AI-generated explanations. Religious references must not be fabricated.

## 2. Recommended technology stack

I would avoid Next.js, React Native, Flutter and heavyweight frameworks for the first release.

A lightweight web application is sufficient. It can become a Progressive Web App (PWA) later.

| Component | Recommended technology | Purpose |
|---|---|---|
| Frontend | Vanilla HTML, CSS, JavaScript | Simple, lightweight interface |
| CSS | Pico.css or vanilla CSS | Responsive, accessible design |
| Backend | Python + FastAPI | API and processing orchestration |
| Database | SQLite | Videos, transcripts, summaries |
| Data format | JSON | Provider-independent AI output |
| Video metadata | YouTube Data API / oEmbed | Video information |
| Media processing | FFmpeg | Audio extraction and conversion |
| Initial transcription | Gemini transcription | Malay speech recognition |
| Alternative transcription | faster-whisper | Local transcription |
| AI summarization | Gemini Flash | Initial AI summarization |
| Future summarization | Qwen 3.x 27B / MoE | Local AI summarization |
| Local model serving | llama.cpp / LM Studio / vLLM | Model inference |
| Task processing | Python background workers | Long-running transcription |
| Deployment | Docker Compose | Simple deployment |
| Version control | GitHub | Source code and documentation |

### Important technology decisions

**A. Gemini ecosystem**

Use Google's official Gemini API rather than making the application dependent on a particular Gemini model.

The current Google documentation describes dedicated transcription capabilities, including:

- Malay-language speech recognition.
- Speaker identification.
- Word-level timestamps.
- Custom vocabulary.
- Verbatim and cleaned-up transcription modes.

See the official documentation: [Gemini audio transcription documentation](https://ai.google.dev/gemini-api/docs/transcribe?hl=en&utm_source=chatgpt.com).

I recommend starting with verbatim transcription because we need to preserve what the speaker actually says. Summarization should be a separate processing stage.

**B. Local AI migration**

Your future hardware target is:

- Ryzen 5 5600G.
- RTX 3060 12GB VRAM.
- 64GB RAM.
- Ubuntu Linux.

Design the application to support two separate AI providers:

| Capability | Initial implementation | Future implementation |
|---|---|---|
| Transcription | Gemini | faster-whisper |
| Summarization | Gemini Flash | Qwen 3.x |
| Question answering | Gemini | Qwen |
| Embeddings | Optional cloud | Local embedding model |
| Storage | SQLite | SQLite |
| API | FastAPI | FastAPI |

Do not assume that a 27B Qwen model will run entirely in your 12GB VRAM. Quantized models may require CPU/RAM offloading. An MoE model can have fewer active parameters per token, but its total weights still need to be stored.

**C. One important architectural decision**

Implement an AI provider interface:

```python
class TranscriptionProvider:
    def transcribe(self, audio_file):
        raise NotImplementedError


class SummaryProvider:
    def summarize(self, transcript):
        raise NotImplementedError


class GeminiTranscription(TranscriptionProvider):
    pass


class WhisperTranscription(TranscriptionProvider):
    pass


class GeminiSummarizer(SummaryProvider):
    pass


class QwenSummarizer(SummaryProvider):
    pass
```

The application should never care whether Gemini or Qwen produced the summary.

This is particularly important when migrating to local models.

---

# 3. Application architecture

```text
                    USER
                      |
                      v
              WEB APPLICATION
             Vanilla HTML/CSS/JS
                      |
                      v
                FASTAPI BACKEND
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
      VIDEO       TRANSCRIPT    DATABASE
     MANAGER       MANAGER      SQLite
          |
          v
     VIDEO SOURCE
     YouTube URL
          |
          v
    METADATA FETCHER
          |
          v
    AUDIO PROCESSING
       FFmpeg
          |
          v
    TRANSCRIPTION ENGINE
          |
      +---+----------------+
      |                    |
      v                    v
    GEMINI             WHISPER
      |                    |
      +---------+----------+
                |
                v
        TRANSCRIPT CLEANUP
                |
                v
         SEGMENT PROCESSOR
                |
                v
        AI SUMMARIZATION
                |
          +-----+------+
          |            |
          v            v
        GEMINI        QWEN
          |            |
          +------+-----+
                 |
                 v
          OUTPUT VALIDATOR
                 |
                 v
          STRUCTURED JSON
                 |
                 v
          SQLITE DATABASE
                 |
                 v
          ACCESSIBLE UI
```

### Processing principle

Do not send an entire long transcript to the summarization model in one request.

Use hierarchical summarization:

1. Divide transcript into manageable segments.
2. Summarize each segment independently.
3. Extract important points from every segment.
4. Combine the segment summaries.
5. Generate the overall summary.
6. Generate topics, FAQ and key takeaways.
7. Validate all timestamps against the original transcript.

This reduces context-window pressure and makes future Qwen deployment easier.

# 4. Functional requirements

## Phase 1 — MVP: Dr. MAZA

**Objective:** Process the initial YouTube video and produce a complete, accessible Malay-language knowledge document.

Source video:

`https://www.youtube.com/watch?v=_eFQiQ9Y06w`

### Video management

- [ ] Accept YouTube video URLs.
- [ ] Validate YouTube URL and extract video ID.
- [ ] Retrieve video title, description, channel and duration.
- [ ] Display video thumbnail.
- [ ] Detect whether captions are available through permitted YouTube interfaces.
- [ ] Support user-provided audio files.
- [ ] Support user-provided transcripts.
- [ ] Store video metadata in SQLite.
- [ ] Prevent duplicate video processing.
- [ ] Maintain processing status.

**Important:** Do not assume that YouTube permits arbitrary downloading or extraction of copyrighted videos. Respect YouTube API policies, content-owner permissions and applicable copyright requirements. Prefer authorized captions, creator-provided material or user-provided media.

### Transcription

- [ ] Implement Gemini transcription provider.
- [ ] Implement Malay language recognition.
- [ ] Preserve original spoken Malay.
- [ ] Preserve Arabic phrases when possible.
- [ ] Recognize common Islamic terminology.
- [ ] Recognize names of scholars and speakers.
- [ ] Generate timestamps.
- [ ] Preserve speaker identification when supported.
- [ ] Detect uncertain or unintelligible phrases.
- [ ] Allow transcript correction.
- [ ] Export transcript as TXT, JSON and SRT.

### Malaysian Malay language intelligence

This is one of the most important components.

Malaysian ceramah is not always delivered in formal Bahasa Melayu.

The system must account for:

- Standard Bahasa Melayu.
- Conversational Malaysian Malay.
- Northern Malaysian dialect influences.
- Kedah and Perlis expressions.
- Kelantan and Terengganu expressions.
- Johor and southern expressions.
- Arabic terminology.
- English and Malay code-switching.

Create a vocabulary dictionary:

`data/dictionaries/malay-islamic-terms.json`

Example:

```json
{
  "terms": [
    {
      "term": "Tadabbur",
      "category": "Islamic",
      "explanation": "Memahami, merenung dan mengambil pengajaran daripada ayat Al-Quran."
    },
    {
      "term": "Istidlal",
      "category": "Islamic",
      "explanation": "Proses menggunakan dalil untuk menyokong sesuatu hujah."
    },
    {
      "term": "Ikhtilaf",
      "category": "Islamic",
      "explanation": "Perbezaan pandangan dalam sesuatu permasalahan."
    }
  ]
}
```

The dictionary should be expandable without modifying application code.

## Phase 2 — AI summarization engine

The application should generate several types of summaries.

| Summary | Description | Priority |
|---|---|---|
| Ringkasan pantas | 5–10 important points | High |
| Ringkasan penuh | Comprehensive lecture summary | High |
| Isi-isi penting | Main arguments and discussions | High |
| Mengikut topik | Topics arranged by section | High |
| FAQ | Questions and answers derived from the lecture | High |
| Istilah penting | Difficult Malay and Arabic terminology | Medium |
| Rujukan agama | Quran and hadith references mentioned | High |
| Pengajaran | Lessons and takeaways | High |
| Glosari | Vocabulary explanations | Medium |

### Summary quality requirements

The AI must follow these rules:

1. Use natural Malaysian Bahasa Melayu.
2. Avoid Indonesian-style vocabulary and sentence structures where natural Malaysian Malay is appropriate.
3. Avoid unnecessarily complicated academic language.
4. Preserve the speaker's original meaning.
5. Do not invent arguments.
6. Do not fabricate Quranic verses or hadith.
7. Clearly distinguish direct statements from AI explanations.
8. Provide timestamps for important discussions.
9. Preserve disagreements and qualifications expressed by the speaker.
10. Flag uncertain religious references for human verification.

### Suggested output format

```json
{
  "video_id": "_eFQiQ9Y06w",
  "speaker": "Dr MAZA",
  "language": "ms-MY",
  "summary": {
    "short": "",
    "detailed": "",
    "key_takeaways": []
  },
  "topics": [
    {
      "title": "",
      "start_time": 0,
      "end_time": 300,
      "summary": "",
      "key_points": []
    }
  ],
  "religious_references": [
    {
      "type": "quran",
      "reference": "",
      "mentioned_at": 0,
      "verification_status": "unverified"
    }
  ],
  "terminology": [],
  "faq": [],
  "transcript": [],
  "quality": {
    "transcription_confidence": null,
    "summary_validation": "pending",
    "human_review": true
  }
}
```

This JSON structure becomes the application's permanent interchange format.

Gemini, Qwen and future AI providers must all produce compatible output.

## Phase 3 — Accessible user interface

Accessibility is not an optional feature. It is the primary reason this application exists.

### Main interface

- [ ] Simple homepage.
- [ ] Search videos.
- [ ] Video listing.
- [ ] Video thumbnail and metadata.
- [ ] Processing status.
- [ ] Summary viewer.
- [ ] Transcript viewer.
- [ ] Topic navigation.
- [ ] Timestamp navigation.
- [ ] FAQ viewer.
- [ ] Download summary as PDF.
- [ ] Download transcript as TXT.
- [ ] Print-friendly summary.

### Accessibility requirements

- [ ] WCAG 2.2 AA design target.
- [ ] Keyboard navigation.
- [ ] Screen reader compatibility.
- [ ] High contrast mode.
- [ ] Adjustable font size.
- [ ] Clear headings.
- [ ] No information communicated exclusively through audio.
- [ ] Responsive desktop and mobile layouts.
- [ ] Captions and transcript displayed alongside video.
- [ ] Easy-to-understand Malay.

### Suggested reading experience

The user should be able to read the lecture without watching the video.

Example:

**Tajuk ceramah:** [Retrieved from YouTube]

**Ringkasan**

A short introduction explaining the central subject of the lecture.

**Isi penting**

1. Perkara pertama yang dibincangkan.
2. Hujah utama yang dikemukakan.
3. Dalil atau rujukan yang disebut.
4. Kesimpulan yang disampaikan.

**Topik perbincangan**

| Timestamp | Topik | Ringkasan |
|---|---|---|
| 00:00 | Pengenalan | Pengenalan kepada perbincangan |
| 05:30 | Perbincangan utama | Hujah dan penjelasan |
| 12:00 | Kesimpulan | Rumusan perbincangan |

Timestamps above are illustrative, not actual video timestamps.

---

# 5. Phase 4 — Multiple Malaysian Ustaz

This phase expands the application beyond Dr. MAZA.

### Supported speakers

Initially:

- Dr. MAZA.
- Other Malaysian ustaz and religious lecturers.

Do not hardcode speakers into the application.

Create a speaker registry:

`data/speakers/speakers.json`

Example:

```json
{
  "speakers": [
    {
      "id": "dr-maza",
      "name": "Dr. MAZA",
      "language": ["ms-MY", "ar"],
      "dialect": "malaysian-malay",
      "enabled": true
    }
  ]
}
```

### Channel management

- [ ] Add YouTube channel.
- [ ] Add individual videos.
- [ ] Support authorized playlists.
- [ ] Discover new videos using permitted YouTube API functionality.
- [ ] Identify new videos.
- [ ] Avoid processing duplicates.
- [ ] Allow administrator approval.
- [ ] Process approved videos.
- [ ] Associate videos with speakers.
- [ ] Maintain speaker-specific vocabulary.

### Future functionality

- Search across all ceramah.
- Search by ustaz.
- Search by topic.
- Search by religious references.
- Search by keywords.
- Compare discussions across different lectures.
- Generate topic-based reading collections.

An important distinction: when comparing different speakers, the application must preserve attribution and never merge their opinions into a single unattributed position.

---

# 6. Phase 5 — Local AI migration

Your eventual objective is to run this application without depending on Gemini.

Design the following provider structure:

```text
app/
  ai/
    providers/
      base.py

      transcription/
        gemini.py
        faster_whisper.py

      summarization/
        gemini.py
        qwen.py

      embeddings/
        local_embeddings.py

    prompts/
      transcript_cleanup.md
      summary_short.md
      summary_detailed.md
      topic_extraction.md
      faq_generation.md
      religious_reference_extraction.md

    schemas/
      transcript.json
      summary.json
```

### Local AI configuration

Create:

`config/ai-providers.yaml`

```yaml
active_providers:

  transcription:
    provider: gemini

  summarization:
    provider: gemini

  embeddings:
    provider: local

providers:

  gemini:
    enabled: true
    model: configurable

  faster_whisper:
    enabled: false
    model: large-v3
    device: cuda
    compute_type: float16

  qwen:
    enabled: false
    endpoint: http://localhost:1234/v1
    model: configurable
    temperature: 0.2
```

Do not hardcode API keys or credentials.

Use environment variables and `.env`.

### Local model considerations

For your RTX 3060 12GB:

| Component | Recommendation |
|---|---|
| Transcription | faster-whisper |
| Small summarization | Qwen 3.x smaller models |
| Larger summarization | Quantized Qwen 27B with CPU/RAM offloading |
| MoE summarization | Compatible quantized Qwen MoE model |
| Model serving | llama.cpp or LM Studio |
| Embeddings | Local embedding model |

Do not assume that every Qwen 27B or MoE release has the same architecture, context requirements or inference compatibility. Test actual model files before selecting one.

The application must work with an OpenAI-compatible local inference endpoint where possible.

---

# 7. Suggested repository structure

Keep the project simple.

```text
ceramah-malaysia/
│
├── README.md
├── AGENTS.md
├── TODO.md
├── ARCHITECTURE.md
├── REQUIREMENTS.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── LICENSE
│
├── frontend/
│   ├── index.html
│   ├── css/
│   │   ├── main.css
│   │   ├── accessibility.css
│   │   └── responsive.css
│   │
│   ├── js/
│   │   ├── app.js
│   │   ├── api.js
│   │   ├── videos.js
│   │   ├── summary.js
│   │   └── transcript.js
│   │
│   └── assets/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   │
│   │   ├── api/
│   │   │   ├── videos.py
│   │   │   ├── summaries.py
│   │   │   ├── transcripts.py
│   │   │   └── speakers.py
│   │   │
│   │   ├── services/
│   │   │   ├── video_service.py
│   │   │   ├── transcription_service.py
│   │   │   ├── summary_service.py
│   │   │   └── processing_service.py
│   │   │
│   │   ├── ai/
│   │   │   ├── providers/
│   │   │   ├── prompts/
│   │   │   └── schemas/
│   │   │
│   │   ├── models/
│   │   ├── database/
│   │   └── workers/
│   │
│   └── requirements.txt
│
├── config/
│   ├── ai-providers.yaml
│   └── application.yaml
│
├── data/
│   ├── dictionaries/
│   │   └── malay-islamic-terms.json
│   ├── speakers/
│   │   └── speakers.json
│   └── database/
│
├── storage/
│   ├── audio/
│   ├── transcripts/
│   └── exports/
│
├── tests/
│   ├── test_transcription.py
│   ├── test_summarization.py
│   ├── test_providers.py
│   ├── test_accessibility.py
│   └── test_api.py
│
├── docker/
│   └── Dockerfile
│
└── docker-compose.yml
```

---

# 8. Agent implementation instructions

The coding agent must follow these instructions.

### Development principles

1. Start with a working MVP, not a complicated architecture.
2. Use Python and vanilla JavaScript.
3. Avoid unnecessary frameworks.
4. Keep dependencies minimal.
5. Use SQLite initially.
6. Keep AI provider implementations independent.
7. Use JSON schemas for AI output validation.
8. Keep prompts in external Markdown files.
9. Write automated tests.
10. Document every environment variable.
11. Provide a `.env.example`.
12. Provide Docker Compose configuration.
13. Never expose Gemini API keys in frontend JavaScript.
14. Never store downloaded media unnecessarily.
15. Support processing recovery after application restarts.

### AI quality control

This project deals with Islamic religious content.

The agent must implement these safeguards:

- Never invent Quranic references.
- Never invent hadith references.
- Never attribute a statement to Dr. MAZA without transcript evidence.
- Never present AI interpretations as the speaker's original words.
- Preserve Arabic quotations when available.
- Mark uncertain Arabic transcription for verification.
- Include timestamps for traceability.
- Allow human correction.
- Preserve the original transcript separately from cleaned transcripts.

### Testing requirements

Create a Malay-language evaluation dataset.

Include:

- Standard Malaysian Malay.
- Northern dialect.
- Arabic terminology.
- Malay-Arabic code-switching.
- Long-form explanations.
- Questions and answers.
- Religious references.
- Names of scholars.

Measure:

| Metric | Purpose |
|---|---|
| WER | Transcription accuracy |
| CER | Character accuracy |
| Reference accuracy | Correct Quran/hadith identification |
| Summary faithfulness | Whether summaries reflect the transcript |
| Timestamp accuracy | Whether sections point to the correct discussion |
| Malay readability | Naturalness of written Malay |
| Hallucination rate | Unsupported statements |

Do not claim the application is accurate simply because the output reads naturally.

---

# 9. Implementation roadmap

I recommend building in six stages.

| Stage | Deliverable | Priority |
|---|---|---|
| 1 | Project foundation and Gemini integration | Critical |
| 2 | Process initial Dr. MAZA video | Critical |
| 3 | Transcript and summary generation | Critical |
| 4 | Accessible reading interface | Critical |
| 5 | Local Qwen and Whisper providers | High |
| 6 | Multiple ustaz and channel management | High |

### MVP acceptance criteria

The MVP is complete when:

- [ ] The supplied YouTube video can be registered.
- [ ] Its metadata can be retrieved.
- [ ] An authorized transcript or audio source can be processed.
- [ ] A Malay transcript is generated.
- [ ] The transcript can be corrected.
- [ ] Short and detailed summaries are generated.
- [ ] Important topics are extracted.
- [ ] Timestamps work.
- [ ] Religious references are clearly marked as verified or unverified.
- [ ] The user can read the entire result without listening to the video.
- [ ] The summary can be exported as PDF.
- [ ] Gemini is isolated behind a provider interface.
- [ ] Automated tests pass.

---

# 10. Additional features worth considering

These are not necessary for the MVP, but could make the application considerably more useful.

**A. Mudah Faham mode**

Allow users to switch between:

- Ringkasan biasa.
- Bahasa Melayu mudah.
- Penjelasan terperinci.

The objective is to make complex discussions easier to understand without changing their original meaning.

**B. Read Along mode**

Display the transcript with highlighted sections synchronized with video timestamps.

Users can jump directly to a particular discussion.

**C. Ceramah knowledge library**

Build a searchable knowledge repository containing:

- All processed lectures.
- Speaker information.
- Main topics.
- Transcripts.
- Summaries.
- References.

SQLite is sufficient initially. Consider a dedicated search index only when the collection grows.

**D. Ask This Ceramah**

Allow users to ask questions about a particular lecture.

Example:

- Apakah tiga perkara utama yang dibincangkan?
- Apakah dalil yang disebut oleh penceramah?
- Pada minit berapa beliau membincangkan perkara tersebut?
- Apakah kesimpulan ceramah ini?

Every answer must include supporting transcript excerpts and timestamps. If the answer cannot be found in the lecture, the application must say so.

**E. Multiple reading formats**

Allow users to choose:

- Ringkasan 1 halaman.
- Nota pembelajaran.
- Artikel panjang.
- Format soal jawab.
- Nota mengikut topik.

---

# 11. Useful open-source resources

These should be evaluated during implementation.

| Project | Purpose | Repository/documentation |
|---|---|---|
| FastAPI | Backend | [FastAPI](https://fastapi.tiangolo.com/?utm_source=chatgpt.com) |
| faster-whisper | Local speech recognition | [faster-whisper](https://github.com/SYSTRAN/faster-whisper/blob/master/README.md?plain=1&utm_source=chatgpt.com) |
| WhisperX | Word alignment and diarization | [WhisperX](https://github.com/m-bain/whisperX?utm_source=chatgpt.com) |
| FFmpeg | Audio processing | [FFmpeg](https://ffmpeg.org/?utm_source=chatgpt.com) |
| SQLite | Database | [SQLite](https://sqlite.org/?utm_source=chatgpt.com) |
| llama.cpp | Local LLM inference | [llama.cpp](https://github.com/ggml-org/llama.cpp?utm_source=chatgpt.com) |
| LM Studio | Local model serving | [LM Studio](https://lmstudio.ai/?utm_source=chatgpt.com) |
| Pico CSS | Lightweight CSS | [Pico CSS](https://picocss.com/?utm_source=chatgpt.com) |

---

# 12. Final architectural recommendation

I would make three decisions from the beginning:

**1. Make Malay language processing the application's speciality.**

Do not build another generic YouTube summarizer. Focus on Malaysian Malay, religious terminology, dialects and Arabic expressions.

**2. Separate transcription from summarization.**

Whisper and Gemini transcription should produce a common transcript format. Gemini and Qwen should consume that same format.

This makes switching AI providers straightforward.

**3. Treat accessibility as the product, not an additional feature.**

A deaf person should be able to obtain the full meaning of a ceramah without depending on audio.

The transcript, summary, topic navigation and references are the actual product.

---

## Suggested project identity

| Item | Recommendation |
|---|---|
| Working name | Ceramah Malaysia |
| Alternative name | FahamCeramah |
| Primary language | Bahasa Melayu |
| Secondary language | English (future) |
| Application type | Web application / PWA |
| Initial AI | Gemini |
| Future AI | Qwen + faster-whisper |
| Backend | FastAPI |
| Frontend | Vanilla JS |
| Database | SQLite |
| Deployment | Docker |
| License | MIT for original application code, subject to third-party dependency and content licensing |

**My preferred name is FahamCeramah.** It communicates the purpose immediately and is not restricted to one speaker or religious organization.

The long-term vision is a searchable, accessible digital library of Malaysian ceramah, preserving knowledge in written form for people who cannot conveniently access spoken content.

---

**Implementation references:** Google's [Gemini transcription API](https://ai.google.dev/gemini-api/docs/transcribe), [Gemini audio understanding](https://ai.google.dev/gemini-api/docs/audio) and [YouTube Developer Policies](https://developers.google.com/youtube/terms/developer-policies).

I recommend giving this entire specification to your coding agent as `TODO.md`, together with `AGENTS.md` instructing it to implement one phase at a time rather than attempting the entire system in one generation.
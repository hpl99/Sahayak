# VOICE FOR LIVELIHOOD — PROJECT HANDOVER

> **Document Type**: Comprehensive Developer & Architecture Handover Guide  
> **Repository**: `voice_livelihood_prototype` (`Sahayak`)  
> **Target Audience**: Incoming developers, peer engineers, and evaluators continuing development in Antigravity / VS Code.  
> **Primary Rule**: Read this document *before* modifying code. Do not refactor or rebuild working architecture casually.

---

## Executive Summary & Problem Statement

**Voice for Livelihood (`Sahayak`)** is an AI-powered multilingual voice assistant and livelihood mapping platform designed for underprivileged citizens and informal-sector workers. It operates under the vision of the **Pradhan Mantri Anusuchit Jaati Abhyuday Yojana (PM-AJAY)** Grant-in-Aid (GIA) skilling component.

### The Problem
Traditional skilling portals rely on text-heavy forms, English/formal terminology, and complex desktop navigation. Informal workers (carpenters, electricians, domestic tailors, daily-wage laborers) struggle with digital literacy and cannot self-identify standard **National Skills Qualifications Framework (NSQF)** trades that match their informal experience and local industrial demand.

### The Objective
Allow any beneficiary to simply **speak** in their native Indian language (Hindi, Marathi, Telugu, Tamil, Bengali, Gujarati). The platform:
1. Listens to unstructured voice answers via **AI4Bharat IndicConformer ASR**.
2. Performs **natural multi-slot profile extraction** to structure their background into a standard Beneficiary Profile.
3. Maps informal background against local district demand and NSQF occupational standards using a transparent **Profile Matcher**.
4. Delivers **spoken voice recommendations** via **TTS** in the beneficiary's language.
5. Enables interactive **course discovery on a dedicated Skill Portal** with a persistent **"Ask Sahayak"** conversational assistant.
6. Connects the full livelihood lifecycle: **Profile $\rightarrow$ Match $\rightarrow$ Explore $\rightarrow$ Resume $\rightarrow$ Training $\rightarrow$ Attendance $\rightarrow$ Follow-up $\rightarrow$ Monitoring**.

```
Beneficiary Voice Input
        │
        ▼ (AI4Bharat IndicConformer ASR)
Spoken Transcript
        │
        ▼ (Multi-Slot Extraction Engine)
Structured Profile (data/profiles.json)
        │
        ▼ (NSQF Matcher + District Demand)
Personalized Recommendations & Explanation
        │
        ▼ (TTS Spoken Output / Web Speech)
Voice & UI Feedback to Citizen
        │
        ▼ (Context-Preserving Handoff)
Interactive Skill Portal ("Ask Sahayak" Voice/Chat)
```

---

## 1. CURRENT PROJECT STATUS

| Feature Area | Status | Nature | Primary Files |
| :--- | :---: | :---: | :--- |
| **Voice Audio Input** | ✅ Active | Real Pipeline | `app.py`, `frontend/voice_assistant/index.html` |
| **IndicConformer ASR (600M)** | ✅ Active | Real AI Model | `speech.py` (`ai4bharat/indic-conformer-600m-multilingual`) |
| **Multilingual Support (6 Langs)** | ✅ Active | Real Engine | `speech.py`, `conversation_manager.py`, `matcher.py` |
| **Conversation Manager** | ✅ Active | Real State Machine | `conversation_manager.py` |
| **Multi-Slot Extraction** | ✅ Active | Real Engine | `conversation_manager.py` (50/50 test verified) |
| **Beneficiary Profile Storage** | ✅ Active | Real Storage | `profile_store.py`, `data/profiles.json` |
| **Profile-Based NSQF Matcher** | ✅ Active | Deterministic Scorer | `matcher.py`, `data/nsqf_trades.csv` |
| **NSQF Trade Data & Demand** | ✅ Active | Representative CSV | `data/nsqf_trades.csv` (12 curated trades) |
| **Spoken Voice Output (TTS)** | ✅ Active | Real (gTTS / Parler) | `speech.py` (fast gTTS with Indic Parler fallback) |
| **Stitch Voice Assistant UI** | ✅ Active | Real Frontend Comp | `frontend/voice_assistant/index.html`, `app.py` |
| **Beneficiary Profile Page** | ✅ Active | Real UI / Storage | `app.py` (Page: `Beneficiary Profile`) |
| **Skill Pathways Page** | ✅ Active | Real UI / Matcher | `app.py` (Page: `Skill Pathways`) |
| **Skill Portal (Courses)** | ✅ Active | Representative Prototype | `skill-portal/index.html`, `static/skill-portal/index.html` |
| **Ask Sahayak (Portal AI)** | ✅ Active | Real Conversational AI | `skill-portal/index.html` (Multilingual Voice/Chat) |
| **Beneficiary Resume Generator** | ✅ Active | Real DOCX Generator | `resume_generator.py`, `app.py` |
| **Training Attendance Integrity** | ✅ Active | Real Phrase Challenge | `attendance_store.py`, `data/attendance.json` |
| **Milestone Follow-up Surveys**| ✅ Active | Real Milestone Engine | `followup_store.py`, `data/followups.json` |
| **Monitoring Dashboard** | ✅ Active | Real Analytics UI | `app.py` (Page: `Dashboard`) |
| **Proof of Work (Computer Vision)** | ⏳ Future | Planned | Architectural placeholder |
| **Live Government API Integration**| ⏳ Future | Planned | Prototype uses representative offline storage |

---

## 2. ARCHITECTURE

```
                    ┌─────────────────────────────────────────┐
                    │       Streamlit Main Application        │
                    │               (app.py)                  │
                    └────────────────────┬────────────────────┘
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
      ┌─────────────────────────────┐             ┌─────────────────────────────┐
      │  Stitch Voice Assistant     │             │  Standard Streamlit Pages   │
      │  Custom HTML/JS Component   │             │  • Beneficiary Profile      │
      │  (frontend/voice_assistant) │             │  • Skill Pathways           │
      └──────────────┬──────────────┘             │  • Resume Generator (.docx) │
                     │ (WAV Base64)               │  • Training Attendance      │
                     ▼                            │  • Milestone Follow-up      │
      ┌─────────────────────────────┐             │  • Monitoring Dashboard     │
      │   Speech Processing Layer   │             └──────────────┬──────────────┘
      │        (speech.py)          │                            │
      │  • IndicConformer ASR       │                            │
      │  • gTTS / Indic Parler-TTS  │                            │
      └──────────────┬──────────────┘                            │
                     │ (Transcript)                              │
                     ▼                                           │
      ┌─────────────────────────────┐                            │
      │    Conversation Manager     │                            │
      │  (conversation_manager.py)  │                            │
      │  • Multi-slot extraction    │                            │
      │  • Dynamic question routing │                            │
      │  • Turn-by-turn persistence │                            │
      └──────────────┬──────────────┘                            │
                     │ (Slots & Profile)                         │
                     ▼                                           │
      ┌──────────────────────────────────────────────────────────┴──────────────┐
      │                      Profile Persistence Layer                          │
      │              (profile_store.py -> data/profiles.json)                   │
      └──────────────────────────────┬──────────────────────────────────────────┘
                                     │
                                     ▼
      ┌─────────────────────────────────────────────────────────────────────────┐
      │                     NSQF Rule & Demand Matcher                          │
      │                 (matcher.py <- data/nsqf_trades.csv)                    │
      └──────────────────────────────┬──────────────────────────────────────────┘
                                     │
                     (Query String Context Propagation)
                     (?beneficiary_id=...&name=...&district=...&lang=...&trade=...)
                                     │
                                     ▼
      ┌─────────────────────────────────────────────────────────────────────────┐
      │                     Standalone Skill Portal                             │
      │        (skill-portal/index.html & static/skill-portal/index.html)       │
      │  • 6 Verified NSQF Course Listings & Syllabus Modules                   │
      │  • Persistent "Ask Sahayak" Multilingual Voice/Chat Assistant            │
      │  • Real-Time Web Speech Recognition & Speech Synthesis (mr, hi, en, etc.)│
      └─────────────────────────────────────────────────────────────────────────┘
```

### Context Propagation Mechanism
When a user finishes onboarding in the Voice Assistant or reviews their profile on the Skill Pathways page, clicking **"Explore on Skill Portal ↗"** opens `/app/static/skill-portal/index.html` (or `skill-portal/index.html`) in a **new browser tab**. The URL query string transmits complete beneficiary context:
- `beneficiary_id`: Unique identifier (e.g. `BEN-2026-001`)
- `name`: Citizen's legal/spoken name (e.g. `Sanjay Verma`)
- `district`: Target district for local demand (e.g. `Wardha` / `Nagpur`)
- `lang`: Active language (e.g. `Marathi` / `Hindi`)
- `trade`: Highlighted NSQF trade (e.g. `Mobile Repair Technician`)
- `skills`: Extracted background skills (e.g. `Screen replacement and soldering`)
- `work`: Prior livelihood experience
- `pref`: Wage vs Self-employment preference

The Skill Portal reads these parameters on `DOMContentLoaded`, highlights the top recommended course, and initializes the **Ask Sahayak** assistant in the beneficiary's exact language.

---

## 3. FILE-BY-FILE GUIDE

### Core Application & Backend
- **[`app.py`](file:///c:/Users/edgeo/Downloads/voice_livelihood_prototype/app.py)** *(Main Streamlit Application)*:
  - **Purpose**: Orchestrates all pages, navigation, global session state, sidebar active beneficiary switcher, and the Stitch Voice Assistant custom component bridge.
  - **Dependencies**: Imports from `speech.py`, `matcher.py`, `profile_store.py`, `conversation_manager.py`, `resume_generator.py`, `attendance_store.py`, `followup_store.py`, `stitch_theme.py`.
  - **Caution**: Contains the component event listener (`last_processed_event_id` deduplication). Do not remove event deduplication logic or session state sync.

- **[`speech.py`](file:///c:/Users/edgeo/Downloads/voice_livelihood_prototype/speech.py)** *(ASR & TTS Engine)*:
  - **Purpose**: Loads AI4Bharat `indic-conformer-600m-multilingual` ASR; handles audio reading via `soundfile` and `scipy` (avoiding fragile torchaudio FFmpeg bindings on Windows); provides dual-mode TTS (fast `gTTS` by default with fallback to `indic-parler-tts`).
  - **Caution**: **PROTECTED CORE**. Do not casually alter model names or audio resampling parameters (target 16 kHz mono).

- **[`conversation_manager.py`](file:///c:/Users/edgeo/Downloads/voice_livelihood_prototype/conversation_manager.py)** *(Conversational State Machine)*:
  - **Purpose**: Manages multi-slot profile extraction, localized question templates (`QUESTIONS` dict across 6 Indian languages), dynamic question routing (skipping already answered slots), and immediate turn persistence.
  - **Caution**: **PROTECTED CORE**. Extraction patterns (`_try_extract_name`, `_try_extract_age`, `_try_extract_work`, `_try_extract_skills`, `_try_extract_preference`) have cross-contamination safeguards between work and skills vocabularies.

- **[`matcher.py`](file:///c:/Users/edgeo/Downloads/voice_livelihood_prototype/matcher.py)** *(NSQF Trade & Demand Matcher)*:
  - **Purpose**: Computes multi-factor match scores using skill keywords (wt 3.0), experience (wt 2.5), interests (wt 2.0), background (wt 1.5), employment preference bonus, and local district demand scores.
  - **Caution**: **PROTECTED CORE**. Generates localized natural language spoken explanations for recommendations.

- **[`profile_store.py`](file:///c:/Users/edgeo/Downloads/voice_livelihood_prototype/profile_store.py)** *(Beneficiary Persistence)*:
  - **Purpose**: Reads/writes structured JSON records in `data/profiles.json`, generates `BEN-YYYY-XXX` IDs, and handles slot updates safely.
  - **Caution**: **PROTECTED CORE**. Single source of truth for beneficiary data.

- **[`resume_generator.py`](file:///c:/Users/edgeo/Downloads/voice_livelihood_prototype/resume_generator.py)** *(DOCX Builder)*:
  - **Purpose**: Generates structured, printable government-formatted one-page `.docx` resumes combining beneficiary details, verified skills, and matched NSQF pathways.

- **[`attendance_store.py`](file:///c:/Users/edgeo/Downloads/voice_livelihood_prototype/attendance_store.py)** *(Voice Attendance)*:
  - **Purpose**: Generates randomized Hindi 4-word challenge phrases (e.g. *"भारत विकास सेवा कौशल"*) and computes fuzzy speech match scores for trainee attendance integrity.

- **[`followup_store.py`](file:///c:/Users/edgeo/Downloads/voice_livelihood_prototype/followup_store.py)** *(Milestone Tracking)*:
  - **Purpose**: Manages post-training livelihood tracking (Day 30, Day 60, Day 180 retention surveys) with an accelerated toggle for live judging demonstrations.

- **[`stitch_theme.py`](file:///c:/Users/edgeo/Downloads/voice_livelihood_prototype/stitch_theme.py)** *(Visual UI Theme & Components)*:
  - **Purpose**: Injects CSS design tokens (Stitch Indigo `#000666`, Saffron `#FF9933`, Surface `#f8f9fa`) and renders reusable HTML widgets (breadcrumbs, completion cards, challenge phrase cards).

### Data Layer
- **[`data/nsqf_trades.csv`](file:///c:/Users/edgeo/Downloads/voice_livelihood_prototype/data/nsqf_trades.csv)**: 12 curated NSQF trades with sector, level, district demand ratings (Nagpur, default), and monthly wage benchmarks.
- **[`data/profiles.json`](file:///c:/Users/edgeo/Downloads/voice_livelihood_prototype/data/profiles.json)**: Local JSON store containing registered citizen profiles.
- **[`data/attendance.json`](file:///c:/Users/edgeo/Downloads/voice_livelihood_prototype/data/attendance.json)**: Trainee daily check-in logs and verification scores.
- **[`data/followups.json`](file:///c:/Users/edgeo/Downloads/voice_livelihood_prototype/data/followups.json)**: Post-training retention survey responses and monthly income logs.

### Frontend & Standalone Prototypes
- **[`frontend/voice_assistant/index.html`](file:///c:/Users/edgeo/Downloads/voice_livelihood_prototype/frontend/voice_assistant/index.html)**: Custom Streamlit bi-directional iframe component. Contains the Stitch pulsing mic UI, live audio capture (MediaRecorder WebM/WAV), dialogue stream, extracted chips container, and direct Skill Portal exploration links.
- **[`skill-portal/index.html`](file:///c:/Users/edgeo/Downloads/voice_livelihood_prototype/skill-portal/index.html)** & **[`static/skill-portal/index.html`](file:///c:/Users/edgeo/Downloads/voice_livelihood_prototype/static/skill-portal/index.html)**: Standalone, responsive NSQF course catalog with 6 realistic courses and the persistent **"Ask Sahayak"** voice/chat drawer supporting 7 Indian languages.

### Tests
- **[`tests/test_context_and_language_fixes.py`](file:///c:/Users/edgeo/Downloads/voice_livelihood_prototype/tests/test_context_and_language_fixes.py)**: 53 tests covering beneficiary context switching, Q1 language initialization, and multilingual Ask Sahayak responses.
- **[`tests/test_multi_slot_extraction.py`](file:///c:/Users/edgeo/Downloads/voice_livelihood_prototype/tests/test_multi_slot_extraction.py)**: 50 tests covering multi-slot extraction, single utterance parsing, and dynamic question routing.
- **[`tests/test_skill_portal.py`](file:///c:/Users/edgeo/Downloads/voice_livelihood_prototype/tests/test_skill_portal.py)**: 17 tests validating Skill Portal courses, context URL parameters, and conversational response simulation.

---

## 4. 🚨 PROTECTED CORE — DO NOT MODIFY CASUALLY

The following 5 files form the critical algorithmic core of the platform:

```
├── speech.py                  (ASR / TTS loading & synthesis)
├── conversation_manager.py    (Slot extractors & state machine)
├── profile_store.py           (Persistence & profile retrieval)
├── matcher.py                 (NSQF trade scoring algorithm)
└── data/nsqf_trades.csv       (Occupational trade dataset)
```

### Current Status Verification
*All 5 core files are verified active and passing regression tests (120/120 tests green).*

### Golden Rule for Protected Core Modifications
Before changing any code in these 5 files:
1. **Understand Why**: Formulate the exact reason a change is required.
2. **Reproduce & Test**: Write a failing unit test in `tests/` reproducing the bug.
3. **Minimal Diff**: Make the smallest possible edit that fixes the verified issue.
4. **Run Full Test Suite**: Run `python tests/test_context_and_language_fixes.py` and `python tests/test_multi_slot_extraction.py`.
5. **Isolate Commit**: Commit the change as its own isolated feature/fix commit.

---

## 5. VOICE PIPELINE SPECIFICATION

```
Citizen Speaks into Microphone
  │
  ▼
Browser MediaRecorder (WebM/WAV audio blob)
  │
  ▼ (Base64 encoded via Streamlit Component Bridge)
speech._load_wav_as_mono_tensor() [SoundFile + SciPy Resampling]
  │
  ▼ (16,000 Hz Mono Float32 Tensor)
ai4bharat/indic-conformer-600m-multilingual [CTC Decoding]
  │
  ▼
Spoken Transcript (e.g. "मेरा नाम रमेश है और मैं वायरिंग का काम करता हूँ")
  │
  ▼
ConversationSession.process_turn()
  │  ├── Guaranteed extractor for asked question
  │  ├── Tentative opportunistic extractors for unfilled slots
  │  └── save_profile() [Immediate Disk Persistence]
  ▼
Next Unanswered Step Question Computed
  │
  ▼
TTS Synthesis Engine (gTTS / Indic Parler-TTS)
  │
  ▼
Spoken Audio (Base64 MP3) Sent to Frontend for Auto-play / Replay
```

### Supported Languages & Codes

| Language | ISO Code | ASR Code | TTS Description Code | Web Speech Synthesis |
| :--- | :---: | :---: | :---: | :---: |
| **Hindi** | `hi` | `hi` | `hi` (Divya voice) | `hi-IN` |
| **Marathi** | `mr` | `mr` | `mr` (Female voice) | `mr-IN` |
| **Telugu** | `te` | `te` | `te` (Female voice) | `te-IN` |
| **Tamil** | `ta` | `ta` | `ta` (Female voice) | `ta-IN` |
| **Bengali** | `bn` | `bn` | `bn` (Female voice) | `bn-IN` |
| **Gujarati** | `gu` | `gu` | `gu` (Female voice) | `gu-IN` |

### Key Architectural Lessons Encountered
1. **Python 3.14 Tokenizers Incompatibility**: Python 3.14 wheels for Hugging Face `tokenizers` and PyO3 caused build crashes. The project runs on **Python 3.13**.
2. **Torchaudio/FFmpeg Windows Issues**: Direct `torchaudio.load()` frequently fails on Windows without external FFmpeg DLLs. `speech.py` uses `soundfile` + `scipy.signal.resample_poly` to read audio files safely.
3. **Lightweight Dual-Mode TTS**: High-latency neural TTS can make local Streamlit demos feel sluggish. `speech.py` uses fast `gTTS` for snappy sub-second audio generation with full fallback support for `indic-parler-tts`.

---

## 6. ENVIRONMENT SETUP (WINDOWS / POWERSHELL)

### Step 1: Ensure Python 3.13
Ensure Python 3.13 is installed:
```powershell
python --version
# Expected output: Python 3.13.x
```

### Step 2: Create & Activate Virtual Environment
```powershell
# In project root: c:\Users\edgeo\Downloads\voice_livelihood_prototype
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Run the Application
```powershell
python -m streamlit run app.py
```
The application will start on `http://localhost:8501`.

### Step 5: Stop the Server & Deactivate
- Press `Ctrl + C` in the terminal to stop the Streamlit server.
- Run `deactivate` to exit the virtual environment.

---

## 7. HUGGING FACE & MODEL DEPENDENCIES

### 1. ASR Model: `ai4bharat/indic-conformer-600m-multilingual`
- **Purpose**: Multilingual Speech Recognition across 22 Indic languages.
- **Size**: ~600M parameters (~2.4 GB download on first run).
- **Access**: Public / Open Access (no special token required).
- **Execution**: Runs on CPU via PyTorch/ONNX or CUDA if available.
- **Cache Directory**: Windows default `C:\Users\<user>\.cache\huggingface\hub`.

### 2. TTS Model: `ai4bharat/indic-parler-tts` *(Optional / Dual Engine)*
- **Purpose**: Neural voice synthesis conditioned on natural language speaker descriptions.
- **Access**: Public repository on Hugging Face.
- **Default Behavior**: If `parler_tts` is not installed, `speech.py` seamlessly falls back to `gTTS`, which requires no model download and operates instantly.

> **Security Note**: Never commit Hugging Face access tokens, API secrets, or private keys to Git.

---

## 8. STREAMLIT STATE MANAGEMENT

### Rerun Mechanics & Global State
Streamlit executes `app.py` from top to bottom on every user action. State continuity is maintained via `st.session_state`:

- `st.session_state.active_beneficiary_id`: **Single source of truth** for the currently selected citizen ID across all pages.
- `st.session_state.selected_language`: Active conversation/UI language.
- `st.session_state.conv_session`: Active `ConversationSession` instance.
- `st.session_state.last_processed_event_id`: Unique UUID to prevent Streamlit from re-executing the same frontend voice turn on page reruns.
- `st.session_state.selected_nav_page`: Active navigation menu selection.

### Verified State Bug Fixes
1. **Event Replay Slot Duplication**:
   - *Issue*: Streamlit component bridge replayed the last event on rerun, causing turn 1 to fill all 5 slots with the same answer.
   - *Fix*: Frontend stamps every event with `event_id: Date.now() + "_" + rand`. Python checks `last_processed_event_id` and discards duplicates.
2. **Stale Active Beneficiary Leakage**:
   - *Issue*: Switching beneficiaries on one page left other pages showing the default demo profile.
   - *Fix*: Centralized `active_beneficiary_id` in session state; sidebar selector and all page dropdowns sync immediately.
3. **Q1 Language Initialization**:
   - *Issue*: Q1 rendered in Hindi even when Marathi was selected before starting conversation.
   - *Fix*: `ConversationSession` honors explicit language arguments on creation, clears TTS question cache on language switch, and frontend DOM default text is dynamically injected.

---

## 9. BENEFICIARY DATA MODEL

Persisted in `data/profiles.json` as an array of JSON dictionaries:

```json
{
  "beneficiary_id": "BEN-2026-001",
  "name": "Ramesh Kumar",
  "age": 26,
  "gender": "Male",
  "district": "Nagpur",
  "education_level": "10th Pass",
  "family_occupation": "Farming / Agriculture",
  "current_livelihood": "Bijli wiring ka kaam (3 years experience)",
  "previous_work_experience": "Electrical helper in local market",
  "skills": "Wiring aur switch fitting",
  "interests": "Electrical appliances repair and industrial wiring",
  "mobility_constraints": "Local only (within district)",
  "employment_preference": "Wage Employment (Job)",
  "language": "Hindi",
  "training_status": "Not Started",
  "training_start_date": null,
  "training_completion_date": null,
  "recommended_trade": "Electrician (Domestic)",
  "created_at": "2026-09-01T10:00:00"
}
```

---

## 10. MATCHING ENGINE LOGIC

The matching engine in `matcher.py` is a **transparent, rule-based and keyword-demand scoring engine** (not black-box ML):

$$\text{Score} = (W_{\text{skill}} \times 3.0) + (W_{\text{exp}} \times 2.5) + (W_{\text{interest}} \times 2.0) + (W_{\text{bg}} \times 1.5) + \text{Bonus}_{\text{pref}} + \text{Score}_{\text{demand}}$$

1. **Skill Overlap ($3.0\times$)**: Token intersection between citizen's stated skills and trade keywords.
2. **Experience Overlap ($2.5\times$)**: Token intersection with previous livelihood experience.
3. **Interest Overlap ($2.0\times$)**: Alignment with citizen's learning aspirations.
4. **Background Overlap ($1.5\times$)**: Current livelihood and family occupation alignment.
5. **Employment Preference ($+1.0$)**: Boost for self-employment trades (e.g. Tailoring, Mobile Repair) vs wage trades (e.g. Welder, Retail Associate).
6. **Local District Demand**: Sourced directly from `demand_<district>` column in `data/nsqf_trades.csv` (1–10 scale).

---

## 11. CONVERSATIONAL ASSISTANT & MULTI-SLOT EXTRACTION

### Natural Multi-Slot Engine
When a citizen speaks naturally:
> *"Mera naam Sunita hai aur main 32 saal ki hoon."*

`ConversationSession.process_turn()` performs:
1. **Guaranteed Extraction**: Extracts the specific field requested for the active step.
2. **Opportunistic Multi-Slot Extraction**: Runs confidence-gated extractors (`_try_extract_name`, `_try_extract_age`, `_try_extract_work`, `_try_extract_skills`, `_try_extract_preference`) on the same utterance.
3. **Immediate Persistence**: Calls `save_profile()` after every turn—no waiting for the conversation to finish.
4. **Dynamic Question Routing**: `current_step` dynamically skips filled slots and queries the first remaining missing field.

---

## 12. SKILL PORTAL & ASK SAHAYAK

- **Path**: `skill-portal/index.html` (and mirrored at `static/skill-portal/index.html`).
- **Catalog**: 6 verified representative NSQF courses:
  1. *Electrician (Domestic)* — NSQF Level 4 (Power)
  2. *Solar Panel Installer (Suryamitra)* — NSQF Level 4 (Green Energy)
  3. *Welder (Fabrication)* — NSQF Level 4 (Manufacturing)
  4. *Mobile Repair Technician* — NSQF Level 3 (Electronics)
  5. *Retail Sales Associate* — NSQF Level 3 (Retail)
  6. *Tailoring & Fashion Design* — NSQF Level 4 (Apparel)
- **Persistent "Ask Sahayak" Assistant**:
  - Floating drawer with real-time **Web Speech Recognition** & **Speech Synthesis**.
  - Supports natural intent queries in **Marathi**, **Hindi**, **English**, etc.:
    - 💡 *"What is this course?"* / *"हा कोर्स काय आहे?"*
    - 🎯 *"Is this suitable for me?"* / *"हा कोर्स माझ्यासाठी योग्य आहे का?"* (personalizes answer using passed citizen profile)
    - 📚 *"What will I learn?"* / *"मी यात काय शिकेन?"*
    - 🔍 *"Show me other courses"* / *"दुसरे कोर्स दाखवा"*
    - 💰 *"Salary & Wages"* / *"पगार किती मिळेल?"*

---

## 13. ⚠️ DATA & GOVERNMENT INTEGRATION RULES

> [!IMPORTANT]
> **Prototype Data Integrity Guidelines**
> 1. Course listings, wage figures, and demand metrics are **representative demonstration data** aligned with NSQF standards.
> 2. The prototype does **not** connect to live NSDC production APIs or live DISCOM hiring databases.
> 3. Always maintain UI disclaimers identifying the portal as a **Demonstration Prototype**.
> 4. Do not state to evaluators or users that enrollment in this prototype guarantees employment without authorized partner center integration.

---

## 14. UI / STITCH DESIGN SYSTEM

The visual interface is built upon the **Stitch Design System**:
- **Design Tokens**:
  - Primary Indigo: `#000666`
  - Container Indigo: `#1a237e`
  - Saffron Highlight: `#FF9933`
  - India Green Badge: `#138808`
  - Clean Surface: `#f8f9fa` / `#ffffff`
  - Outline Borders: `#c6c5d4`
- **Typography**: Inter & Google Fonts.
- **Icons**: Material Symbols Outlined.
- **Reference UI Assets**: Located under `stitch-ui/` (`beneficiary_profile_1`, `beneficiary_resume`, `post_training_follow_up`, `skill_pathways`).

---

## 15. APPLICATION PAGE SITEMAP

1. **🎙️ Voice Assistant**: Interactive conversational onboarding with pulsing mic and real-time profile slot extraction.
2. **🧭 Skill Pathways**: Profile-matched NSQF pathways, local demand scores, wage benchmarks, and direct Skill Portal links.
3. **👤 Beneficiary Profile**: Comprehensive CRUD editor for citizen background, education, and mobility details.
4. **📄 Resume Generator**: One-click `.docx` resume builder formatted for employer submission.
5. **🎓 Training Modules**: NSQF course curriculum directory with enrollment tracking.
6. **📅 Training Follow-up**: Post-training milestone tracker (Day 30, 60, 180) with accelerated demo mode.
7. **✅ Attendance Integrity**: Trainee presence verification using randomized spoken Hindi challenge phrases.
8. **📊 Monitoring Dashboard**: Administrative metrics on total onboarded citizens, sector distribution, and wage averages.
9. **🌐 Standalone Skill Portal**: Dedicated web portal (`skill-portal/index.html`) with course syllabus cards and "Ask Sahayak" voice advisor.

---

## 16. TEST SUITE EXECUTION

Run all automated test suites using the active virtual environment:

```powershell
# 1. Context, language initialization, and multilingual Ask Sahayak tests (53 tests)
python tests/test_context_and_language_fixes.py

# 2. Multi-slot extraction & backward compatibility tests (50 tests)
python tests/test_multi_slot_extraction.py

# 3. Skill Portal integrity, courses, and link construction tests (17 tests)
python tests/test_skill_portal.py
```

**Total Verified Tests**: **120 passed / 0 failed**.

---

## 17. KNOWN ISSUES & CURRENT STATUS

| Issue | Severity | Status | Technical Notes |
| :--- | :---: | :---: | :--- |
| **Model Cold-Start Download** | Low | Expected | Initial download of IndicConformer (~2.4 GB) takes 1–3 mins on fresh machines. |
| **Browser Speech Permission** | Low | Expected | Browser must be granted microphone access when opening the Skill Portal for voice recognition. |
| **Parler-TTS Flash Attention Notice**| Info | Non-fatal | Parler-TTS outputs PyTorch attention warning on CPU; falls back gracefully to standard attention or gTTS. |

---

## 18. DEVELOPER DO'S

- ✅ **Inspect First**: Check `git status`, test suites, and existing files before writing code.
- ✅ **Preserve Core Pipeline**: Keep ASR $\rightarrow$ Profile $\rightarrow$ Match $\rightarrow$ TTS flow intact.
- ✅ **Run Tests Frequently**: Execute all 3 test scripts after every code modification.
- ✅ **Keep Beneficiary State Centralized**: Always read/write `st.session_state.active_beneficiary_id`.
- ✅ **Support Multilingual Inputs**: Verify Marathi, Hindi, and regional language handling when adding questions.
- ✅ **Make Isolated Commits**: Commit completed features individually with clear descriptive messages.

---

## 19. DEVELOPER DON'TS

- ❌ **Do NOT Hardcode Active Beneficiary**: Never hardcode `"Ramesh Kumar"` as the active citizen.
- ❌ **Do NOT Hardcode Hindi as Permanent Language**: Always honor the beneficiary's chosen language.
- ❌ **Do NOT Modify Protected Core Casually**: Do not alter `speech.py`, `matcher.py`, or `profile_store.py` without reproduction tests.
- ❌ **Do NOT Replace Working Models**: Keep existing IndicConformer ASR configuration.
- ❌ **Do NOT Revert Stitch UI to Generic Streamlit**: Preserve custom Stitch CSS tokens and frontend components.
- ❌ **Do NOT Commit Credentials or Tokens**: Never push private Hugging Face tokens or API keys.

---

## 20. GIT WORKFLOW & HISTORY

### Recent Git Commit History
- `2dc3dd9`: `fix: repair beneficiary context and multilingual voice state` *(Active beneficiary sync across pages, Marathi/Hindi Ask Sahayak engine, language initialization)*
- `e6d76fc`: `feat: add isolated skill portal prototype with persistent Ask Sahayak conversational assistant` *(6 courses, persistent voice drawer, context forwarding)*
- `4fac130`: `feat: persistent natural multi-slot extraction` *(Single-turn multi-slot parser, dynamic routing, immediate turn persistence)*
- `6dc0a2d`: `fix: repair voice conversation state and responsive ui` *(Event deduplication bridge, step counter fix)*
- `f4d36d1`: `feat: integrate stitch voice assistant frontend` *(Bi-directional Streamlit component)*

### Standard Contribution Workflow
```powershell
git status
git pull origin master
# Make focused changes
python tests/test_context_and_language_fixes.py
python tests/test_multi_slot_extraction.py
git diff
git add <modified_files>
git commit -m "feat: description of verified feature"
git push origin master
```

---

## 21. HOW TO CONTINUE DEVELOPMENT SAFELY

Follow this 10-step development cycle:
1. **Read**: Review this `PROJECT_HANDOVER.md`.
2. **Check State**: Run `git status` to verify a clean working tree.
3. **Verify Baseline**: Run all 3 test scripts in `tests/`.
4. **Launch Application**: Start `python -m streamlit run app.py` and test the target page.
5. **Plan Change**: Write a minimal implementation plan before modifying files.
6. **Implement**: Edit only the necessary files.
7. **Re-Test**: Run the test suite to verify zero regressions.
8. **Inspect Diff**: Review `git diff` to ensure no unintended files or whitespace changes occurred.
9. **Commit**: Create a single, isolated commit.
10. **Update Handover**: Update `PROJECT_HANDOVER.md` if data schemas or architectures change.

---

## 22. PRODUCT ROADMAP

### Implemented (Active & Verified)
- Bi-directional Multilingual Voice Assistant (6 Indian languages).
- Instant multi-slot profile extraction and turn-by-turn persistence.
- Profile-based NSQF demand matching with localized spoken explanations.
- Centralized active beneficiary propagation across 8 pages.
- Standalone Skill Portal with persistent "Ask Sahayak" voice/chat advisor.
- DOCX Resume generation, Challenge Phrase Attendance, and Follow-up survey engine.

### Next Recommended Enhancements
1. **Computer Vision Proof of Work**: Add photo upload and automated tool/craft verification for artisan beneficiaries.
2. **Direct Center Locator**: Map local training centers in Nagpur / Vidarbha region with GPS navigation coordinates.
3. **WhatsApp / SMS Summary Dispatch**: Export course recommendations and resume links directly via Twilio / Gupshup SMS.

### Future Advanced AI / ML
- Semantic embedding matching using domain-finetuned BERT / sentence-transformers on NSQF occupational standards.
- Speech-to-speech low-latency streaming pipeline.

---

## 23. DEMO & EVALUATION SCRIPT

When demonstrating the platform to evaluators or judges:
1. **Voice Assistant**: Open Voice Assistant in **Marathi** or **Hindi**. Click the mic and speak:
   > *"Mera naam Sanjay Verma hai aur meri umar 28 saal hai."*
2. **Multi-Slot Verification**: Observe that both Name (Sanjay Verma) and Age (28) fill immediately in the Extracted Information panel, and the assistant skips straight to Question 3 (Work Experience).
3. **Recommendation**: Complete the conversation and view top matched NSQF pathways (e.g. *Electrician Domestic* or *Mobile Repair*).
4. **Skill Portal Exploration**: Click **"Explore on Skill Portal ↗"**.
5. **Ask Sahayak**: On the Skill Portal, click the pulsing mic or prompt chip:
   > *"हा कोर्स माझ्यासाठी योग्य आहे का?"* or *"What will I learn?"*
   Hear and read the personalized response generated in the citizen's native language.
6. **Full Lifecycle**: Return to main app, open **Beneficiary Profile**, **Resume**, **Attendance**, and **Monitoring Dashboard** to show end-to-end data synchronization.

---

## 24. TROUBLESHOOTING GUIDE

| Problem | Cause | Solution |
| :--- | :--- | :--- |
| `ModuleNotFoundError: No module named 'soundfile'` | Virtual environment not active | Run `.\venv\Scripts\Activate.ps1` and `pip install -r requirements.txt`. |
| `Python 3.14 PyO3 build error` | Python version too new for prebuilt wheels | Switch to Python 3.13. |
| `SpeechRecognition not supported` | Browser speech recognition restricted | Use Chrome / Edge or type in text input fallback box. |
| `Streamlit Port 8501 in use` | Previous instance still running | Run `python -m streamlit run app.py --server.port 8502`. |
| `Question audio does not replay` | Browser blocked autoplay | Click the **"Hear question (TTS)"** button. |

---

## 25. SECURITY & PRIVACY

- **Storage**: Citizen data is stored locally in `data/profiles.json`.
- **Offline / Local Execution**: ASR and profile matching run entirely on local compute.
- **Privacy Standard**: No beneficiary PII is transmitted to third-party commercial tracking services.

---

## 26. QUICK START — NEW DEVELOPER CHEATSHEET

```powershell
# 1. Clone repository
git clone https://github.com/hpl99/Sahayak.git
cd Sahayak

# 2. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 3. Verify test baseline
python tests/test_context_and_language_fixes.py
python tests/test_multi_slot_extraction.py
python tests/test_skill_portal.py

# 4. Launch Application
python -m streamlit run app.py

# 5. Open in browser
# Main Portal: http://localhost:8501
# Skill Portal: http://localhost:8501/app/static/skill-portal/index.html
```

# Voice for Livelihood — Skilling & Retention Ecosystem
**Smart India Hackathon — Problem Statement 26097**

An end-to-end, voice-first livelihood support prototype tailored for rural and informal workers in India. Beneficiaries speak their background and interests in regional languages, receive NSQF-aligned skilling recommendations matched to local job demand with transparent reasoning, generate standardized resumes, complete anti-replay attendance check-ins, and track long-term employment retention over 30, 60, and 180 days.

---

## 🏛️ System Architecture

``` 
[ Beneficiary Voice Input ]
           │
           ▼
[ AI4Bharat Indic Conformer ASR (Offline/Open-Source) ]
           │
           ▼ (Transcript & Speech Tokens)
 ┌─────────────────────────────────────────────────────────┐
 │             Livelihood Intelligence Core                │
 │  • Transcript Keyword & Local Demand Matcher            │
 │  • Profile Multidimensional Matcher (Skills/Wage/Demand)│
 │  • Explainable Rationale Engine ("Recommended because") │
 └────────────────────────────┬────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
[ NSQF Trade Path ]  [ 1-Page DOCX Resume ]  [ Post-Training Milestones ]
          │                                  (30d / 60d / 180d Follow-up)
          ▼                                       │
[ Indic Parler-TTS ]                              ▼
          │                                  [ Re-Skilling Trigger ]
          ▼                                  (If not employed, suggest next trade)
[ Spoken Response ]
```

---

## 📁 Project Structure

```
├── app.py                  Streamlit multi-page UI (6 modular views)
├── speech.py               ASR + TTS wrappers (AI4Bharat Indic Conformer & Indic Parler-TTS) [PROTECTED]
├── matcher.py              Keyword + profile matcher with transparent reasoning
├── profile_store.py        Beneficiary profile manager with local JSON persistence
├── resume_generator.py     One-page DOCX resume builder (python-docx)
├── followup_store.py       Post-training 30/60/180-day retention tracker & Demo Mode
├── attendance_store.py     Anti-replay dynamic phrase challenge verification
├── DEMO_SCRIPT.md          5-minute Hackathon presentation guide
├── requirements.txt        Python dependencies
└── data/
    ├── nsqf_trades.csv     NSQF trade database with keywords, wages & district demand scores
    ├── profiles.json       Persistent beneficiary records
    ├── followups.json      Post-training milestone check-ins & survey responses
    └── attendance.json     Trainee attendance challenge check-in logs
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10 – 3.13
- Internet access during initial run to cache Hugging Face model weights (~2 GB). Subsequent runs operate completely offline.

### Quickstart

```bash
# 1. Create and activate virtual environment
python -m venv venv
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
pip install git+https://github.com/huggingface/parler-tts.git

# 3. Launch the Streamlit application
streamlit run app.py
```

---

## 🌟 Feature Overview

### 1. 🎙️ Voice Recommendation (Core Engine)
- Zero-friction audio recording or WAV clip upload.
- **ASR**: High-accuracy transcription using `ai4bharat/indic-conformer-600m-multilingual`.
- **Matching**: Matches transcripts against NSQF Level 3/4 trades weighted by local district demand (e.g., Nagpur).
- **TTS**: Synthesizes spoken regional responses using `ai4bharat/indic-parler-tts` across Hindi, Marathi, Telugu, Tamil, Bengali, and Gujarati.

### 2. 👤 Beneficiary Profile System
- Local JSON storage in `data/profiles.json` (no external database required).
- Tracks education level, family occupation, current livelihood, mobility constraints, employment preference (wage vs self-employment), and language.
- Full CRUD interface: Create, search/lookup, edit, and view beneficiary records.

### 3. 🎯 Profile-Based Matching & Explainable AI
- Evaluates complete profile attributes against the NSQF database.
- Provides transparent justifications for every recommendation:
  ```
  Recommended because:
  ✓ Stated skill matches: bijli, wiring, switch
  ✓ High local demand in Nagpur (9/10)
  ✓ Matches wage-employment preference with structured hiring
  ✓ Education background (10th Pass) fits NSQF Level 4
  ```

### 4. 📄 One-Page DOCX Livelihood Resume
- Generates a single-page formatted `.docx` resume from profile data and top skilling pathways.
- Downloadable for job applications and Skill India counseling centers.

### 5. 📅 Post-Training Follow-Up & Retention Tracking
- Initializes **30-day**, **60-day**, and **180-day** milestones upon marking training complete.
- **⚡ DEMO MODE**: Accelerates timeline (30s / 60s / 180s instead of days) for live hackathon judging.
- 4-question outcome survey (employment status, training alignment, monthly wage, re-skilling interest).
- **Dynamic Re-Skilling Trigger**: If a beneficiary reports not working, the system flags `⚠️ Previous recommendation did not result in employment` and automatically generates secondary recommendations.

### 6. 🛡️ Attendance Integrity Demo
- Generates dynamic 4-digit challenge phrases per check-in (e.g., `"Eight Four One One" / "आठ चार एक एक"`).
- Trainee speaks the phrase; verified using the existing on-device ASR model to prevent static audio replay attacks.
- Explicit prototype disclaimer: *Voice identity verification is not implemented; challenge-response prevents replay.*

### 7. 📊 Livelihood Monitoring Dashboard
- Program-wide visibility into total beneficiaries, training completion rates, employment outcomes, average wages, and attendance compliance.

---

## ⚡ Demo Mode Guide

1. In sidebar navigation, open **"📅 Training Follow-up"**.
2. Ensure **"⚡ DEMO MODE"** is toggled ON.
3. Mark training complete for any beneficiary.
4. Watch the 30-second live countdown timer for Milestone 1.
5. Submit a survey response with `"No"` for employment to demonstrate the automatic re-skilling workflow.

---

## ⚠️ Prototype Scope & Limitations

| Feature | Prototype Status | Production Roadmap |
|---|---|---|
| **Data Storage** | Local JSON (`data/*.json`) | SQLite / PostgreSQL |
| **Follow-up Calls** | In-app simulated survey & countdown | Cloud IVR / Exotel / Twilio Webhook |
| **Attendance** | Dynamic phrase anti-replay check | Voice biometric speaker verification |
| **Demand Feed** | Local district score index (`nsqf_trades.csv`) | Real-time state labor market API feed |

---

## 🤖 Open-Source Models Used

| Task | Model | Source | License |
|---|---|---|---|
| **ASR** | `ai4bharat/indic-conformer-600m-multilingual` | Hugging Face / AI4Bharat | MIT |
| **TTS** | `ai4bharat/indic-parler-tts` | Hugging Face / AI4Bharat | Apache-2.0 |

Both models run entirely offline once downloaded with zero per-query API fees.

# Voice for Livelihood — Prototype

A minimal, end-to-end demo for Problem Statement 26097: speak your background
and interests in a regional language, get an NSQF-aligned skilling
recommendation matched to local job demand, spoken back to you.

**Pipeline:** mic/audio input → IndicConformer (ASR) → keyword + local-demand
matcher → NSQF trade recommendation → Indic Parler-TTS (spoken reply)

This is deliberately scoped to one complete loop, not the full production
system (no IVR, no WhatsApp, no live labour-market feed) — see "Level up"
below for what to add if you have time.

## Project structure

```
app.py              Streamlit UI — wires everything together
speech.py           ASR + TTS wrapper functions (AI4Bharat models)
matcher.py          Keyword-overlap + local-demand trade matching (no ML needed)
data/nsqf_trades.csv  Sample trade database with bilingual keywords + mock demand scores
requirements.txt
```

## Setup

Requires internet access to huggingface.co the first time you run it (to
download model weights — a few GB total). After the first run, models are
cached locally.

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
pip install git+https://github.com/huggingface/parler-tts.git

streamlit run app.py
```

A GPU is not required but makes both ASR and TTS noticeably faster. On CPU,
expect a few seconds per transcription and 10-20 seconds per TTS reply —
fine for a live demo, just don't let judges watch a spinner for too long
without narrating what's happening.

## Before your demo

- **Run it once fully, end to end, the night before** — the first call to
  each model downloads weights, which you don't want happening live.
- **Pre-record 2-3 sample audio clips** in your target languages (use the
  file uploader as a fallback if live mic recording is flaky on the venue's
  wifi/laptop).
- **Screen-record a full successful run** as a backup video. If the live
  demo breaks, you switch to video and keep talking.
- Try a few different sample sentences yourself against `matcher.py`
  directly (`python matcher.py`) to get a feel for which keywords land —
  it'll help you pick phrasing that demos well.

## Testing the matcher without any ML dependencies

```bash
python matcher.py
```

This runs a sample Hinglish transcript through the matcher and prints the
top 3 trade matches — useful for tuning `data/nsqf_trades.csv` without
waiting on model downloads.

## Level up (if you have time before judging)

Roughly in order of effort-to-impact:

1. **More trades / richer keywords** — the current CSV has 12 trades and
   hand-picked keywords. Expanding this (and adding real district demand
   data instead of mock scores) is the highest-leverage, lowest-effort win.
2. **Semantic matching instead of keyword overlap** — swap `matcher.py`'s
   keyword scoring for sentence-embedding similarity
   (`sentence-transformers` with a multilingual model, e.g.
   `paraphrase-multilingual-MiniLM-L12-v2`) so it still matches when the
   beneficiary doesn't use your exact keywords.
3. **Translation layer** — run the ASR transcript through IndicTrans2 into
   English before matching, so you only maintain one English trade
   database instead of bilingual keyword lists per trade.
4. **Follow-up turn** — let the app ask one clarifying question ("Would you
   prefer self-employment or a job?") before giving the final
   recommendation, to show the "conversational, not a form" framing.
5. **A second, mock "outcome check-in" screen** — a tiny second page that
   simulates the 30/90/180-day follow-up call concept from the pitch deck.

## Models used

| Task | Model | License |
|---|---|---|
| ASR | `ai4bharat/indic-conformer-600m-multilingual` | MIT |
| TTS | `ai4bharat/indic-parler-tts` | Apache-2.0 |

Both are open-source, from AI4Bharat, and run entirely offline once
downloaded — no per-call API cost, which is worth mentioning to judges as
a cost/scalability point for a government deployment.

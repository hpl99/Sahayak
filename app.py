"""
Voice for Livelihood -- prototype demo

Pipeline:

Voice input
    ↓
Indic Conformer ASR
    ↓
Transcript
    ↓
Keyword + local demand matcher
    ↓
NSQF trade recommendation
    ↓
Multilingual recommendation text
    ↓
Indic Parler-TTS
    ↓
Spoken response
"""

import os
import tempfile

import streamlit as st

from matcher import (
    load_trades,
    match_trades,
    build_recommendation_text,
)

from speech import (
    LANGUAGES,
    load_asr_model,
    transcribe,
    load_tts_model,
    synthesize,
)


# ---------------------------------------------------------------------------
# PAGE
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Voice for Livelihood",
    page_icon="🎙️",
    layout="centered",
)


DISTRICTS = [
    "Nagpur",
    "Default (any district)",
]


# ---------------------------------------------------------------------------
# CACHED MODEL LOADERS
# ---------------------------------------------------------------------------

@st.cache_resource(
    show_spinner=(
        "Loading speech recognition model "
        "(first run only)..."
    )
)
def get_asr_model():

    return load_asr_model()


@st.cache_resource(
    show_spinner=(
        "Loading text-to-speech model "
        "(first run only)..."
    )
)
def get_tts_bundle():

    return load_tts_model()


@st.cache_data
def get_trades_df():

    return load_trades(
        os.path.join(
            "data",
            "nsqf_trades.csv",
        )
    )


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

st.title("🎙️ Voice for Livelihood")

st.caption(
    "Prototype — speak your background and interests, "
    "get an NSQF-aligned skilling recommendation matched "
    "to local demand, spoken back to you."
)


# ---------------------------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------------------------

with st.sidebar:

    st.header("Settings")

    language_label = st.selectbox(
        "Language",
        list(LANGUAGES.keys()),
        index=0,
    )

    lang_code = LANGUAGES[
        language_label
    ]

    district = st.selectbox(
        "District (for local demand matching)",
        DISTRICTS,
        index=0,
    )

    district_key = (
        "default"
        if district.startswith("Default")
        else district.lower()
    )

    decoding = st.radio(
        "ASR decoding",
        ["ctc", "rnnt"],
        index=0,
        help=(
            "ctc is faster, rnnt is usually more accurate"
        ),
    )

    st.divider()

    st.caption(
        "Models: "
        "ai4bharat/indic-conformer-600m-multilingual "
        "(ASR) · "
        "ai4bharat/indic-parler-tts (TTS)"
    )


# ---------------------------------------------------------------------------
# RECORDING
# ---------------------------------------------------------------------------

st.subheader("1. Speak or upload your response")

st.write(
    f'Try answering in **{language_label}**: '
    f'"What work have you done before, '
    f'and what would you like to learn?"'
)


audio_value = st.audio_input(
    "Record your answer"
)

uploaded_file = st.file_uploader(
    "...or upload a short WAV/FLAC clip instead",
    type=["wav", "flac"],
)


audio_bytes = None


if audio_value is not None:

    audio_bytes = audio_value.getvalue()

elif uploaded_file is not None:

    audio_bytes = uploaded_file.getvalue()


run = st.button(
    "Transcribe & Recommend",
    type="primary",
    disabled=audio_bytes is None,
)


# ---------------------------------------------------------------------------
# PROCESS AUDIO
# ---------------------------------------------------------------------------

if run and audio_bytes is not None:

    tmp_path = None

    try:

        # ---------------------------------------------------------------
        # Save temporary input audio
        # ---------------------------------------------------------------

        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False,
        ) as tmp:

            tmp.write(audio_bytes)

            tmp_path = tmp.name


        # ---------------------------------------------------------------
        # ASR
        # ---------------------------------------------------------------

        with st.spinner(
            "Transcribing..."
        ):

            asr_model = get_asr_model()

            transcript = transcribe(
                asr_model,
                tmp_path,
                lang_code,
                decoding,
            )


        st.subheader(
            "2. What we heard"
        )

        st.info(transcript)


        # ---------------------------------------------------------------
        # TRADE MATCHING
        # ---------------------------------------------------------------

        with st.spinner(
            "Matching to NSQF trades and local demand..."
        ):

            trades_df = get_trades_df()

            matches = match_trades(
                transcript,
                district=district_key,
                trades_df=trades_df,
                top_n=3,
            )


        st.subheader(
            "3. Recommended pathways"
        )


        for i, m in enumerate(
            matches,
            start=1,
        ):

            with st.container(
                border=True
            ):

                st.markdown(
                    f"**{i}. {m['trade_name']}**  · "
                    f"NSQF Level {m['nsqf_level']}  · "
                    f"{m['sector']}"
                )

                cols = st.columns(3)

                cols[0].metric(
                    "Local demand score",
                    f"{m['demand_score']:.0f}/10",
                )

                cols[1].metric(
                    "Avg monthly wage",
                    f"₹{m['avg_monthly_wage_inr']:,}",
                )

                cols[2].metric(
                    "Matched keywords",
                    len(m["matched_keywords"]),
                )

                if m["matched_keywords"]:

                    st.caption(
                        "Matched on: "
                        + ", ".join(
                            m["matched_keywords"]
                        )
                    )


        # ---------------------------------------------------------------
        # MULTILINGUAL RECOMMENDATION
        # ---------------------------------------------------------------

        reply_text = build_recommendation_text(
            matches,
            language_label,
        )


        st.subheader(
            "4. Spoken recommendation"
        )

        # Show exactly what will be spoken.
        st.write(reply_text)


        # ---------------------------------------------------------------
        # TTS
        # ---------------------------------------------------------------

        with st.spinner(
            f"Generating spoken reply in {language_label}..."
        ):

            tts_bundle = get_tts_bundle()

            out_path = os.path.join(
                tempfile.gettempdir(),
                "voice_livelihood_reply.wav",
            )

            out_path = synthesize(
                tts_bundle,
                reply_text,
                lang_code,
                out_path=out_path,
            )


        # ---------------------------------------------------------------
        # PLAY AUDIO
        # ---------------------------------------------------------------

        st.audio(
            out_path,
            format="audio/wav",
        )

        st.success(
            f"Spoken response generated in {language_label}."
        )


    except Exception as e:

        st.error(
            "Something went wrong while processing "
            "the voice response."
        )

        st.exception(e)


    finally:

        if (
            tmp_path is not None
            and os.path.exists(tmp_path)
        ):

            try:
                os.unlink(tmp_path)
            except OSError:
                pass


elif not audio_bytes:

    st.caption(
        "Record or upload audio, then press "
        "**Transcribe & Recommend**."
    )
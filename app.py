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
    match_profile,
    build_recommendation_text,
)

from speech import (
    LANGUAGES,
    load_asr_model,
    transcribe,
    load_tts_model,
    synthesize,
)

from profile_store import (
    load_profiles,
    get_profile,
    save_profile,
    list_profiles,
    generate_beneficiary_id,
)

from resume_generator import (
    generate_resume_docx,
    generate_resume_preview_text,
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
# NAVIGATION
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("Navigation")
    page = st.radio(
        "Go to",
        [
            "🎙️ Voice Recommendation",
            "👤 Beneficiary Profile",
            "📄 Resume",
        ],
        index=0,
    )
    st.divider()


# ===========================================================================
# PAGE 1: VOICE RECOMMENDATION (ORIGINAL DEMO - 100% PRESERVED)
# ===========================================================================

if page == "🎙️ Voice Recommendation":

    st.title("🎙️ Voice for Livelihood")

    st.caption(
        "Prototype — speak your background and interests, "
        "get an NSQF-aligned skilling recommendation matched "
        "to local demand, spoken back to you."
    )

    # -----------------------------------------------------------------------
    # SETTINGS
    # -----------------------------------------------------------------------

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

    # -----------------------------------------------------------------------
    # RECORDING
    # -----------------------------------------------------------------------

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

    # -----------------------------------------------------------------------
    # PROCESS AUDIO
    # -----------------------------------------------------------------------

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


# ===========================================================================
# PAGE 2: BENEFICIARY PROFILE (FEATURE 1)
# ===========================================================================

elif page == "👤 Beneficiary Profile":

    st.title("👤 Beneficiary Profile")
    st.caption("Manage persistent beneficiary records stored locally in data/profiles.json.")

    profiles = load_profiles()

    profile_mode = st.radio(
        "Action",
        ["Create New Beneficiary", "Lookup / Edit Existing Beneficiary"],
        horizontal=True,
    )

    selected_profile = None

    if profile_mode == "Lookup / Edit Existing Beneficiary":
        if not profiles:
            st.info("No beneficiary profiles found yet. Please create a new beneficiary.")
        else:
            profile_options = {
                f"{p.get('beneficiary_id', '')} - {p.get('name', 'Unnamed')} ({p.get('district', '')})": p.get("beneficiary_id")
                for p in profiles
            }
            selected_label = st.selectbox("Select Beneficiary", list(profile_options.keys()))
            selected_id = profile_options[selected_label]
            selected_profile = get_profile(selected_id)

    # Determine default values
    if selected_profile:
        current_id = selected_profile.get("beneficiary_id")
        def_name = selected_profile.get("name", "")
        def_age = int(selected_profile.get("age", 25))
        def_gender = selected_profile.get("gender", "Male")
        def_district = selected_profile.get("district", "Nagpur")
        def_edu = selected_profile.get("education_level", "10th Pass")
        def_fam = selected_profile.get("family_occupation", "")
        def_live = selected_profile.get("current_livelihood", "")
        def_skills = selected_profile.get("skills", "")
        def_interests = selected_profile.get("interests", "")
        def_mobility = selected_profile.get("mobility_constraints", "Local only (within district)")
        def_emp = selected_profile.get("employment_preference", "Wage Employment (Job)")
        def_lang = selected_profile.get("language", "Hindi")
        def_status = selected_profile.get("training_status", "Not Started")
        def_trade = selected_profile.get("recommended_trade", "") or ""
    else:
        current_id = generate_beneficiary_id()
        def_name = ""
        def_age = 24
        def_gender = "Male"
        def_district = "Nagpur"
        def_edu = "10th Pass"
        def_fam = ""
        def_live = ""
        def_skills = ""
        def_interests = ""
        def_mobility = "Local only (within district)"
        def_emp = "Wage Employment (Job)"
        def_lang = "Hindi"
        def_status = "Not Started"
        def_trade = ""

    st.subheader(f"Profile: {current_id}")

    with st.form("beneficiary_profile_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Full Name", value=def_name)
            age = st.number_input("Age", min_value=14, max_value=75, value=def_age)
            gender = st.selectbox(
                "Gender",
                ["Male", "Female", "Other", "Prefer not to say"],
                index=["Male", "Female", "Other", "Prefer not to say"].index(def_gender) if def_gender in ["Male", "Female", "Other", "Prefer not to say"] else 0,
            )
            district = st.selectbox(
                "District",
                ["Nagpur", "Pune", "Mumbai", "Amravati", "Nashik", "Aurangabad", "Default (any district)"],
                index=["Nagpur", "Pune", "Mumbai", "Amravati", "Nashik", "Aurangabad", "Default (any district)"].index(def_district) if def_district in ["Nagpur", "Pune", "Mumbai", "Amravati", "Nashik", "Aurangabad", "Default (any district)"] else 0,
            )
            language = st.selectbox(
                "Preferred Language",
                list(LANGUAGES.keys()),
                index=list(LANGUAGES.keys()).index(def_lang) if def_lang in LANGUAGES else 0,
            )
            education_level = st.selectbox(
                "Education Level",
                ["No formal education", "5th Pass", "8th Pass", "10th Pass", "12th Pass", "ITI / Diploma", "Graduate", "Post Graduate"],
                index=["No formal education", "5th Pass", "8th Pass", "10th Pass", "12th Pass", "ITI / Diploma", "Graduate", "Post Graduate"].index(def_edu) if def_edu in ["No formal education", "5th Pass", "8th Pass", "10th Pass", "12th Pass", "ITI / Diploma", "Graduate", "Post Graduate"] else 3,
            )

        with col2:
            family_occupation = st.text_input("Family Occupation / Background", value=def_fam)
            current_livelihood = st.text_input("Current Livelihood / Occupation", value=def_live)
            mobility_constraints = st.selectbox(
                "Mobility Constraints",
                ["Local only (within district)", "Willing to relocate within state", "Willing to relocate anywhere in India"],
                index=["Local only (within district)", "Willing to relocate within state", "Willing to relocate anywhere in India"].index(def_mobility) if def_mobility in ["Local only (within district)", "Willing to relocate within state", "Willing to relocate anywhere in India"] else 0,
            )
            employment_preference = st.selectbox(
                "Employment Preference",
                ["Wage Employment (Job)", "Self Employment (Entrepreneurship / Micro-enterprise)", "Either / Any"],
                index=["Wage Employment (Job)", "Self Employment (Entrepreneurship / Micro-enterprise)", "Either / Any"].index(def_emp) if def_emp in ["Wage Employment (Job)", "Self Employment (Entrepreneurship / Micro-enterprise)", "Either / Any"] else 0,
            )
            training_status = st.selectbox(
                "Training Status",
                ["Not Started", "In Progress", "Completed"],
                index=["Not Started", "In Progress", "Completed"].index(def_status) if def_status in ["Not Started", "In Progress", "Completed"] else 0,
            )
            recommended_trade = st.text_input("Recommended Trade (if assigned)", value=def_trade)

        skills = st.text_area(
            "Skills & Work Experience (e.g. electrical wiring, switch repair, plumbing, driving)",
            value=def_skills,
            help="Enter key skills or previous informal work experience.",
        )
        interests = st.text_area(
            "Interests & Learning Aspirations (e.g. solar panel installation, machine maintenance)",
            value=def_interests,
            help="Enter trades or skills the beneficiary is interested in learning.",
        )

        submitted = st.form_submit_button("Save / Update Profile", type="primary")

        if submitted:
            if not name.strip():
                st.warning("Please enter a name for the beneficiary.")
            else:
                profile_payload = {
                    "beneficiary_id": current_id,
                    "name": name.strip(),
                    "age": int(age),
                    "gender": gender,
                    "district": district,
                    "education_level": education_level,
                    "family_occupation": family_occupation.strip(),
                    "current_livelihood": current_livelihood.strip(),
                    "skills": skills.strip(),
                    "interests": interests.strip(),
                    "mobility_constraints": mobility_constraints,
                    "employment_preference": employment_preference,
                    "language": language,
                    "training_status": training_status,
                    "training_start_date": selected_profile.get("training_start_date") if selected_profile else None,
                    "training_completion_date": selected_profile.get("training_completion_date") if selected_profile else None,
                    "recommended_trade": recommended_trade.strip() if recommended_trade else None,
                    "created_at": selected_profile.get("created_at") if selected_profile else None,
                }
                saved = save_profile(profile_payload)
                st.success(f"Profile for {saved['name']} ({saved['beneficiary_id']}) saved successfully!")

    # Display active profile summary
    active_profile = get_profile(current_id)
    if active_profile:
        st.divider()
        st.subheader(f"Current Profile Record: {active_profile.get('beneficiary_id')}")
        with st.container(border=True):
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**Name:** {active_profile.get('name')}")
                st.write(f"**Age / Gender:** {active_profile.get('age')} / {active_profile.get('gender')}")
                st.write(f"**District:** {active_profile.get('district')}")
                st.write(f"**Education:** {active_profile.get('education_level')}")
                st.write(f"**Language:** {active_profile.get('language')}")
            with col_b:
                st.write(f"**Current Livelihood:** {active_profile.get('current_livelihood') or 'None specified'}")
                st.write(f"**Family Occupation:** {active_profile.get('family_occupation') or 'None specified'}")
                st.write(f"**Mobility:** {active_profile.get('mobility_constraints')}")
                st.write(f"**Employment Pref:** {active_profile.get('employment_preference')}")
                st.write(f"**Training Status:** {active_profile.get('training_status')}")

            st.write(f"**Skills:** {active_profile.get('skills') or 'None entered'}")
            st.write(f"**Interests:** {active_profile.get('interests') or 'None entered'}")
            if active_profile.get("recommended_trade"):
                st.info(f"**Assigned / Recommended Trade:** {active_profile.get('recommended_trade')}")

        # Profile-Based Trade Recommendations
        st.subheader("🎯 Profile-Based Skilling Recommendations")
        trades_df = get_trades_df()
        profile_matches = match_profile(
            active_profile,
            trades_df=trades_df,
            district=active_profile.get("district", "Nagpur"),
            top_n=3,
        )

        for i, m in enumerate(profile_matches, start=1):
            with st.container(border=True):
                st.markdown(
                    f"**{i}. {m['trade_name']}** · "
                    f"NSQF Level {m['nsqf_level']} · "
                    f"{m['sector']}"
                )
                cols = st.columns(3)
                cols[0].metric("Local demand score", f"{m['demand_score']:.0f}/10")
                cols[1].metric("Avg monthly wage", f"₹{m['avg_monthly_wage_inr']:,}")
                cols[2].metric("Match score", f"{m['score']:.1f}")

                st.markdown("**Recommended because:**")
                for exp in m["explanations"]:
                    st.write(exp)

    # Display list of all registered beneficiaries
    all_profiles = list_profiles()
    if all_profiles:
        st.divider()
        st.subheader(f"All Registered Beneficiaries ({len(all_profiles)})")
        summary_table = [
            {
                "ID": p.get("beneficiary_id"),
                "Name": p.get("name"),
                "Age": p.get("age"),
                "District": p.get("district"),
                "Education": p.get("education_level"),
                "Current Work": p.get("current_livelihood"),
                "Training Status": p.get("training_status"),
            }
            for p in all_profiles
        ]
        st.dataframe(summary_table, use_container_width=True)


# ===========================================================================
# PAGE 3: RESUME (FEATURE 3)
# ===========================================================================

elif page == "📄 Resume":

    st.title("📄 Beneficiary Resume Generator")
    st.caption("Generate a structured one-page DOCX resume from the saved beneficiary profile and skilling recommendations.")

    profiles = load_profiles()

    if not profiles:
        st.info("No beneficiary profiles found. Please create a profile in the 'Beneficiary Profile' section first.")
    else:
        profile_options = {
            f"{p.get('beneficiary_id', '')} - {p.get('name', 'Unnamed')} ({p.get('district', '')})": p.get("beneficiary_id")
            for p in profiles
        }
        selected_label = st.selectbox("Select Beneficiary for Resume", list(profile_options.keys()))
        selected_id = profile_options[selected_label]
        profile = get_profile(selected_id)

        if profile:
            trades_df = get_trades_df()
            recs = match_profile(
                profile,
                trades_df=trades_df,
                district=profile.get("district", "Nagpur"),
                top_n=3,
            )

            # Generate DOCX binary data
            docx_data = generate_resume_docx(profile, recs)
            safe_name = str(profile.get("name", "beneficiary")).replace(" ", "_")
            file_name = f"Resume_{profile.get('beneficiary_id')}_{safe_name}.docx"

            col_btn1, col_btn2 = st.columns([2, 3])
            with col_btn1:
                st.download_button(
                    label="📥 Download Resume (.docx)",
                    data=docx_data,
                    file_name=file_name,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary",
                )

            st.divider()
            st.subheader("Resume Preview")

            with st.container(border=True):
                st.markdown(
                    f"### SKILL INDIA — BENEFICIARY RESUME\n"
                    f"**Beneficiary ID:** `{profile.get('beneficiary_id')}` | "
                    f"**District:** {profile.get('district')} | "
                    f"**Language:** {profile.get('language')}"
                )
                st.divider()

                st.markdown("#### 1. Personal & Background Information")
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    st.write(f"**Full Name:** {profile.get('name')}")
                    st.write(f"**Age / Gender:** {profile.get('age')} / {profile.get('gender')}")
                    st.write(f"**Education Level:** {profile.get('education_level')}")
                with col_r2:
                    st.write(f"**Current Livelihood:** {profile.get('current_livelihood') or 'None specified'}")
                    st.write(f"**Family Occupation:** {profile.get('family_occupation') or 'None specified'}")
                    st.write(f"**Mobility:** {profile.get('mobility_constraints')}")

                st.write(f"**Employment Preference:** {profile.get('employment_preference')}")

                st.divider()
                st.markdown("#### 2. Skills & Aspirations")
                st.write(f"• **Stated Skills & Experience:** {profile.get('skills') or 'None specified'}")
                st.write(f"• **Learning Goals & Interests:** {profile.get('interests') or 'None specified'}")

                st.divider()
                st.markdown("#### 3. Recommended NSQF Skilling Pathways")
                for i, r in enumerate(recs, 1):
                    st.markdown(
                        f"**{i}. {r['trade_name']}** (NSQF Level {r['nsqf_level']} · {r['sector']}) — "
                        f"Avg Wage: ₹{r['avg_monthly_wage_inr']:,} | Demand: {r['demand_score']:.0f}/10"
                    )
                    for exp in r.get("explanations", []):
                        st.caption(f"   {exp}")

                st.divider()
                st.markdown("#### 4. Training Status")
                st.write(f"**Current Status:** {profile.get('training_status', 'Not Started')}")
                if profile.get("recommended_trade"):
                    st.write(f"**Assigned Trade:** {profile.get('recommended_trade')}")
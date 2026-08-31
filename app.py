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

from followup_store import (
    load_followups,
    get_beneficiary_followups,
    mark_training_complete,
    record_survey_response,
    get_milestone_timing,
)

from attendance_store import (
    load_attendance,
    save_attendance_record,
    generate_challenge_phrase,
    verify_phrase_match,
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
            "📅 Training Follow-up",
            "🛡️ Attendance Integrity",
            "📊 Monitoring Dashboard",
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
        def_prev_exp = selected_profile.get("previous_work_experience", "")
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
        def_prev_exp = ""
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
            previous_work_experience = st.text_input("Previous Work Experience", value=def_prev_exp)
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
            "Skills & Practical Experience (e.g. electrical wiring, switch repair, plumbing, driving)",
            value=def_skills,
            help="Enter key skills or practical abilities.",
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
                    "previous_work_experience": previous_work_experience.strip(),
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
                st.write(f"**Previous Experience:** {active_profile.get('previous_work_experience') or 'None specified'}")
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


# ===========================================================================
# PAGE 4: TRAINING FOLLOW-UP (FEATURE 4)
# ===========================================================================

elif page == "📅 Training Follow-up":

    st.title("📅 Post-Training Livelihood Follow-up")
    st.info(
        "⚠️ **DEMO / PROTOTYPE**: Automated post-training milestone simulation for Smart India Hackathon. "
        "Simulates 30-day, 60-day, and 180-day retention calls without external IVR/telecom dependencies."
    )

    demo_mode = st.toggle(
        "⚡ DEMO MODE (Accelerate timeline: 30s / 60s / 180s instead of days)",
        value=True,
        help="When enabled, milestones become active in seconds rather than months for live judging demonstration.",
    )

    profiles = load_profiles()

    if not profiles:
        st.info("No beneficiary profiles found. Please create a profile in the 'Beneficiary Profile' section first.")
    else:
        profile_options = {
            f"{p.get('beneficiary_id', '')} - {p.get('name', 'Unnamed')} ({p.get('district', '')})": p.get("beneficiary_id")
            for p in profiles
        }
        selected_label = st.selectbox("Select Beneficiary to Monitor", list(profile_options.keys()))
        selected_id = profile_options[selected_label]
        profile = get_profile(selected_id)

        if profile:
            st.divider()
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                st.write(f"**Beneficiary:** {profile.get('name')} (`{profile.get('beneficiary_id')}`)")
                st.write(f"**District / Language:** {profile.get('district')} / {profile.get('language')}")
                st.write(f"**Assigned Trade:** {profile.get('recommended_trade') or 'Electrician (Domestic)'}")
            with col_t2:
                status = profile.get("training_status", "Not Started")
                st.write(f"**Current Status:** `{status}`")
                comp_date = profile.get("training_completion_date")
                if comp_date:
                    st.write(f"**Completed On:** {comp_date[:19].replace('T', ' ')}")

            # Action: Mark Training Complete
            if status != "Completed":
                st.warning("Training is currently in progress or not started. Mark training complete to activate follow-up milestones.")
                trade_to_assign = profile.get("recommended_trade") or "Electrician (Domestic)"
                trade_input = st.text_input("Trade Completed", value=trade_to_assign)
                if st.button("✅ Mark Training Complete", type="primary"):
                    mark_training_complete(selected_id, trade_input)
                    st.success(f"Training marked complete for {profile.get('name')}! Milestones generated.")
                    st.rerun()
            else:
                st.subheader("Post-Training Milestones")
                milestones = get_beneficiary_followups(selected_id)

                if not milestones:
                    # Initialize milestones if not present
                    milestones = mark_training_complete(selected_id, profile.get("recommended_trade"))

                for idx, m in enumerate(milestones, 1):
                    timing = get_milestone_timing(m, demo_mode=demo_mode)
                    is_completed = m.get("status") == "Completed"
                    is_due = timing["is_due"]

                    with st.container(border=True):
                        st.markdown(f"### Milestone {idx}: {m.get('milestone')} Check-in")
                        st.caption(f"Status: **{timing['status_label']}**")

                        if is_completed:
                            st.success("✅ Survey response recorded:")
                            resp = m.get("survey_response", {})
                            c1, c2 = st.columns(2)
                            with c1:
                                st.write(f"• **Currently Working:** {resp.get('is_working')}")
                                st.write(f"• **Work Related to Training:** {resp.get('work_related_to_training')}")
                            with c2:
                                st.write(f"• **Monthly Income:** ₹{resp.get('monthly_income_inr', 0):,}")
                                st.write(f"• **Wants New Recommendation:** {resp.get('wants_new_recommendation')}")

                            # Outcome Action: If not working, trigger re-recommendation
                            if resp.get("is_working") == "No" or resp.get("wants_new_recommendation") == "Yes":
                                st.warning("⚠️ **Outcome Alert:** Previous recommendation did not result in employment.")
                                st.markdown("#### Next Best Skilling Pathways:")
                                trades_df = get_trades_df()
                                new_matches = match_profile(
                                    profile,
                                    trades_df=trades_df,
                                    district=profile.get("district", "Nagpur"),
                                    top_n=3,
                                )
                                # Filter out previously trained trade if possible to show alternatives
                                alt_matches = [
                                    nm for nm in new_matches
                                    if nm["trade_name"].lower() != str(m.get("trade_name", "")).lower()
                                ]
                                display_matches = alt_matches if alt_matches else new_matches

                                for r_i, r_m in enumerate(display_matches[:2], 1):
                                    st.info(
                                        f"**Alternative {r_i}: {r_m['trade_name']}** "
                                        f"(NSQF Level {r_m['nsqf_level']} · {r_m['sector']})\n\n"
                                        f"• Local Demand: {r_m['demand_score']:.0f}/10 | Avg Wage: ₹{r_m['avg_monthly_wage_inr']:,}\n\n"
                                        f"• Reason: {r_m['explanation_text'].replace(chr(10), ' | ')}"
                                    )
                        else:
                            st.write("Record the beneficiary's answers to the follow-up questions:")
                            with st.form(f"survey_form_{m.get('followup_id')}"):
                                q1 = st.radio(
                                    "1. Are you currently working?",
                                    ["Yes", "No"],
                                    horizontal=True,
                                    key=f"q1_{m.get('followup_id')}",
                                )
                                q2 = st.radio(
                                    "2. Is your work related to your training?",
                                    ["Yes", "Somewhat", "No"],
                                    horizontal=True,
                                    key=f"q2_{m.get('followup_id')}",
                                )
                                q3 = st.number_input(
                                    "3. What is your approximate monthly income (₹)?",
                                    min_value=0,
                                    max_value=200000,
                                    value=12000 if q1 == "Yes" else 0,
                                    step=500,
                                    key=f"q3_{m.get('followup_id')}",
                                )
                                q4 = st.radio(
                                    "4. Would you like another recommendation?",
                                    ["No", "Yes"],
                                    horizontal=True,
                                    key=f"q4_{m.get('followup_id')}",
                                )

                                submit_survey = st.form_submit_button(
                                    f"Submit {m.get('milestone')} Response",
                                    type="primary",
                                )

                                if submit_survey:
                                    response_data = {
                                        "is_working": q1,
                                        "work_related_to_training": q2,
                                        "monthly_income_inr": int(q3),
                                        "wants_new_recommendation": q4,
                                    }
                                    record_survey_response(m.get("followup_id"), response_data)
                                    st.success("Follow-up survey response saved successfully!")
                                    st.rerun()

                # Table of all follow-ups
                st.divider()
                st.subheader("All Follow-up Tracking Records")
                all_followups = load_followups()
                if all_followups:
                    summary_fol = [
                        {
                            "ID": f.get("followup_id"),
                            "Beneficiary": f.get("beneficiary_id"),
                            "Trade": f.get("trade_name"),
                            "Milestone": f.get("milestone"),
                            "Status": f.get("status"),
                            "Working?": f.get("survey_response", {}).get("is_working", "Pending") if f.get("survey_response") else "Pending",
                            "Income": f"₹{f.get('survey_response', {}).get('monthly_income_inr', 0):,}" if f.get("survey_response") else "-",
                        }
                        for f in all_followups
                    ]
                    st.dataframe(summary_fol, use_container_width=True)


# ===========================================================================
# PAGE 5: ATTENDANCE INTEGRITY (FEATURE 5)
# ===========================================================================

elif page == "🛡️ Attendance Integrity":

    st.title("🛡️ Trainee Attendance Integrity Check")
    st.warning(
        "⚠️ **DEMO / PROTOTYPE**: Voice identity verification is not implemented. "
        "This prototype uses dynamic challenge-response phrase verification with the existing ASR pipeline "
        "to prevent static audio replay attacks in low-bandwidth training attendance check-ins."
    )

    profiles = load_profiles()

    if not profiles:
        st.info("No beneficiary profiles found. Please create a profile in the 'Beneficiary Profile' section first.")
    else:
        profile_options = {
            f"{p.get('beneficiary_id', '')} - {p.get('name', 'Unnamed')} ({p.get('district', '')})": p.get("beneficiary_id")
            for p in profiles
        }
        selected_label = st.selectbox("Select Trainee for Check-in", list(profile_options.keys()))
        selected_id = profile_options[selected_label]
        profile = get_profile(selected_id)

        # Initialize session state for challenge phrase if needed
        if "current_challenge" not in st.session_state:
            st.session_state.current_challenge = generate_challenge_phrase(4)

        challenge = st.session_state.current_challenge

        st.divider()
        st.subheader("1. Dynamic Spoken Challenge")
        st.caption("The trainee must speak the randomly generated phrase below to complete verification.")

        with st.container(border=True):
            st.markdown(f"### 🗣️ \"{challenge['phrase_en']}\"")
            st.write(f"• **Digits:** `{challenge['digits_str']}`")
            st.write(f"• **Hindi / Regional Phrasing:** {challenge['phrase_hi']}")

            if st.button("🔄 Generate New Challenge Phrase"):
                st.session_state.current_challenge = generate_challenge_phrase(4)
                st.rerun()

        st.subheader("2. Speak Challenge Phrase")
        st.write("Record your voice speaking the dynamic challenge phrase above:")

        att_audio_input = st.audio_input("Record challenge phrase")
        att_file_upload = st.file_uploader("...or upload recorded WAV clip", type=["wav", "flac"], key="att_uploader")

        att_bytes = None
        if att_audio_input is not None:
            att_bytes = att_audio_input.getvalue()
        elif att_file_upload is not None:
            att_bytes = att_file_upload.getvalue()

        verify_btn = st.button("🎙️ Transcribe & Verify Attendance", type="primary", disabled=att_bytes is None)

        if verify_btn and att_bytes is not None:
            tmp_att_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_att:
                    tmp_att.write(att_bytes)
                    tmp_att_path = tmp_att.name

                with st.spinner("Transcribing spoken challenge with AI4Bharat Indic Conformer ASR..."):
                    asr_model = get_asr_model()
                    lang_code = LANGUAGES.get(profile.get("language", "Hindi"), "hi")
                    att_transcript = transcribe(asr_model, tmp_att_path, lang_code, "ctc")

                st.subheader("3. Verification Result")
                st.write(f"**Expected Phrase:** `{challenge['expected_phrase']}`")
                st.write(f"**Transcribed Speech:** `{att_transcript}`")

                status, flagged, match_score, reason = verify_phrase_match(challenge["digits"], att_transcript)

                record_data = {
                    "beneficiary_id": selected_id,
                    "expected_phrase": challenge["expected_phrase"],
                    "transcript": att_transcript,
                    "status": status,
                    "flagged": flagged,
                    "match_score": match_score,
                    "reason": reason,
                    "demo_note": "Demo attendance integrity — voice identity verification not implemented",
                }
                saved_rec = save_attendance_record(record_data)

                if status == "Pass" and not flagged:
                    st.success(f"✅ **Attendance Verified (PASS)** — {reason} (Score: {match_score:.0%})")
                elif status == "Pass" and flagged:
                    st.warning(f"⚠️ **Attendance Recorded (FLAGGED FOR REVIEW)** — {reason} (Score: {match_score:.0%})")
                else:
                    st.error(f"❌ **Attendance Rejected (FAIL)** — {reason} (Score: {match_score:.0%})")

                # Generate fresh challenge for next check-in
                st.session_state.current_challenge = generate_challenge_phrase(4)

            except Exception as e:
                st.error("Error during attendance transcription and verification.")
                st.exception(e)
            finally:
                if tmp_att_path is not None and os.path.exists(tmp_att_path):
                    try:
                        os.unlink(tmp_att_path)
                    except OSError:
                        pass

        # Attendance Log & Summary
        st.divider()
        st.subheader("Trainee Attendance Dashboard")
        all_att = load_attendance()
        if all_att:
            total_att = len(all_att)
            passed_att = sum(1 for a in all_att if a.get("status") == "Pass")
            failed_att = sum(1 for a in all_att if a.get("status") == "Fail")
            flagged_att = sum(1 for a in all_att if a.get("flagged") is True)

            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("Total Check-ins", total_att)
            m_col2.metric("Verified (Pass)", passed_att)
            m_col3.metric("Rejected (Fail)", failed_att)
            m_col4.metric("Flagged for Review", flagged_att)

            st.write("Recent Attendance Records:")
            att_table = [
                {
                    "Record ID": a.get("record_id"),
                    "Trainee": a.get("beneficiary_id"),
                    "Timestamp": a.get("timestamp", "")[:19].replace("T", " "),
                    "Expected": a.get("expected_phrase"),
                    "Transcribed": a.get("transcript"),
                    "Status": a.get("status"),
                    "Flagged": "⚠️ Yes" if a.get("flagged") else "No",
                }
                for a in reversed(all_att)
            ]
            st.dataframe(att_table, use_container_width=True)


# ===========================================================================
# PAGE 6: MONITORING DASHBOARD (FEATURE 6)
# ===========================================================================

elif page == "📊 Monitoring Dashboard":

    st.title("📊 Livelihood Monitoring Dashboard")
    st.caption(
        "Aggregated program analytics for SIH PS 26097: beneficiary enrollment, "
        "training completions, post-training employment retention, and attendance integrity."
    )

    profiles = load_profiles()
    followups = load_followups()
    attendance = load_attendance()
    trades_df = get_trades_df()

    # Section 1: Beneficiary & Skilling Overview
    st.subheader("1. Beneficiary Enrollment & Training Progress")
    total_b = len(profiles)
    completed_train = sum(1 for p in profiles if p.get("training_status") == "Completed")
    in_progress_train = sum(1 for p in profiles if p.get("training_status") == "In Progress")
    not_started_train = sum(1 for p in profiles if p.get("training_status") == "Not Started")
    assigned_trades = sum(1 for p in profiles if p.get("recommended_trade"))

    b_col1, b_col2, b_col3, b_col4 = st.columns(4)
    b_col1.metric("Total Beneficiaries", total_b)
    b_col2.metric("Training Completed", completed_train)
    b_col3.metric("Training In Progress", in_progress_train)
    b_col4.metric("Assigned Pathways", assigned_trades)

    st.divider()

    # Section 2: Post-Training Follow-up & Employment Outcomes
    st.subheader("2. Post-Training Employment & Retention Outcomes")
    total_fol = len(followups)
    completed_fol = sum(1 for f in followups if f.get("status") == "Completed")
    
    working_count = 0
    unemployed_count = 0
    incomes = []

    for f in followups:
        resp = f.get("survey_response")
        if resp:
            if resp.get("is_working") == "Yes":
                working_count += 1
                inc = resp.get("monthly_income_inr", 0)
                if inc > 0:
                    incomes.append(inc)
            elif resp.get("is_working") == "No":
                unemployed_count += 1

    avg_inc = sum(incomes) / len(incomes) if incomes else 0

    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    f_col1.metric("Follow-ups Completed", completed_fol)
    f_col2.metric("Employed Post-Training", working_count)
    f_col3.metric("Seeking Re-skilling", unemployed_count)
    f_col4.metric("Avg Monthly Income", f"₹{avg_inc:,.0f}" if avg_inc > 0 else "N/A")

    st.divider()

    # Section 3: Attendance Integrity Metrics
    st.subheader("3. Trainee Attendance Integrity Check Overview")
    total_att = len(attendance)
    passed_att = sum(1 for a in attendance if a.get("status") == "Pass")
    failed_att = sum(1 for a in attendance if a.get("status") == "Fail")
    flagged_att = sum(1 for a in attendance if a.get("flagged") is True)

    a_col1, a_col2, a_col3, a_col4 = st.columns(4)
    a_col1.metric("Attendance Attempts", total_att)
    a_col2.metric("Verified (Pass)", passed_att)
    a_col3.metric("Rejected (Fail)", failed_att)
    a_col4.metric("Flagged for Review", flagged_att)

    st.divider()

    # Section 4: Data Tables
    st.subheader("4. Detailed Records & District Demand")

    tab1, tab2, tab3 = st.tabs(["Beneficiaries", "NSQF Trade Demand", "Follow-up Surveys"])

    with tab1:
        if profiles:
            p_table = [
                {
                    "ID": p.get("beneficiary_id"),
                    "Name": p.get("name"),
                    "District": p.get("district"),
                    "Education": p.get("education_level"),
                    "Preference": p.get("employment_preference"),
                    "Status": p.get("training_status"),
                    "Trade": p.get("recommended_trade") or "General",
                }
                for p in profiles
            ]
            st.dataframe(p_table, use_container_width=True)
        else:
            st.info("No beneficiary records yet.")

    with tab2:
        st.dataframe(trades_df[["trade_name", "sector", "nsqf_level", "demand_nagpur", "demand_default", "avg_monthly_wage_inr"]], use_container_width=True)

    with tab3:
        if followups:
            fol_table = [
                {
                    "Follow-up ID": f.get("followup_id"),
                    "Beneficiary": f.get("beneficiary_id"),
                    "Trade": f.get("trade_name"),
                    "Milestone": f.get("milestone"),
                    "Status": f.get("status"),
                    "Working?": f.get("survey_response", {}).get("is_working", "-") if f.get("survey_response") else "-",
                    "Income": f"₹{f.get('survey_response', {}).get('monthly_income_inr', 0):,}" if f.get("survey_response") else "-",
                }
                for f in followups
            ]
            st.dataframe(fol_table, use_container_width=True)
        else:
            st.info("No follow-up records yet.")
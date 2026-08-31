"""
Stitch Design System theme and UI helpers for Voice for Livelihood.

Implements Google Stitch Material 3 design tokens:
- Primary Navy (#1A237E / #000666)
- Surface Canvas (#FBF9F8)
- High-legibility Inter Typography
- Google Material Symbols Outlined
- Bento card containers, dynamic completion calculations, and exact Stitch layout tokens.
"""

from typing import Any, Dict, List, Tuple
import streamlit as st

STITCH_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

    /* Google Stitch Base Theme */
    html, body, [class*="css"], .stMarkdown, .stText, p, span, label, div {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* Main background canvas */
    .stApp {
        background-color: #FBF9F8 !important;
        color: #1B1C1C !important;
    }

    /* Top Padding & Container Width */
    .main .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1180px !important;
    }

    /* Hide default Streamlit header bar decoration */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* Top and Sidebar Headers */
    h1, h2, h3, h4 {
        color: #000666 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #F6F3F2 !important;
        border-right: 1px solid #C6C5D4 !important;
        padding-top: 1.25rem !important;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 1rem !important;
    }

    /* Navigation Radio Items in Sidebar */
    section[data-testid="stSidebar"] [data-testid="stRadio"] label {
        font-size: 15px !important;
        font-weight: 500 !important;
        color: #454652 !important;
        padding: 6px 10px !important;
        border-radius: 8px !important;
        transition: all 0.15s ease !important;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
        background-color: #EAE8E7 !important;
        color: #000666 !important;
    }

    /* Buttons */
    .stButton > button {
        background-color: #000666 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 0.375rem !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        padding: 0.55rem 1.25rem !important;
        transition: all 0.15s ease-in-out !important;
    }
    .stButton > button:hover {
        background-color: #1A237E !important;
        color: #FFFFFF !important;
        transform: scale(0.99) !important;
    }

    /* Secondary / outline buttons */
    .stButton > button[kind="secondary"] {
        background-color: #FFFFFF !important;
        color: #000666 !important;
        border: 2px solid #000666 !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background-color: #F0EDED !important;
    }

    /* Form Inputs */
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox select {
        border: 1.5px solid #C6C5D4 !important;
        border-radius: 0.375rem !important;
        background-color: #FFFFFF !important;
        color: #1B1C1C !important;
        font-size: 14px !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #000666 !important;
        box-shadow: 0 0 0 2px rgba(0, 6, 102, 0.1) !important;
    }

    /* Stitch Container Cards */
    .stitch-card {
        background-color: #FFFFFF;
        border: 1px solid #C6C5D4;
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }

    /* Breadcrumbs */
    .stitch-breadcrumb {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        font-size: 14px;
        color: #454652;
        margin-bottom: 0.75rem;
    }
    .stitch-breadcrumb span.current {
        font-weight: 600;
        color: #1B1C1C;
    }

    /* Demo Mode Badge */
    .stitch-demo-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        background-color: #E0E0FF;
        color: #000767;
        font-size: 12px;
        font-weight: 600;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        border: 1px solid #BDC2FF;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }

    /* Profile Completion Progress */
    .stitch-progress-container {
        background-color: #EAE8E7;
        border-radius: 9999px;
        height: 10px;
        width: 100%;
        overflow: hidden;
        margin-top: 0.75rem;
    }
    .stitch-progress-bar {
        background-color: #000666;
        height: 100%;
        border-radius: 9999px;
        transition: width 0.3s ease;
    }

    /* Status Badges & Pills */
    .stitch-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        background-color: #F0EDED;
        border: 1px solid #C6C5D4;
        padding: 0.3rem 0.7rem;
        border-radius: 9999px;
        font-size: 13px;
        font-weight: 500;
        color: #1B1C1C;
    }

    /* Assistant Message Bubble */
    .stitch-assistant-bubble {
        background-color: #E0E0FF;
        color: #000767;
        border: 1px solid #BDC2FF;
        border-radius: 1rem 1rem 1rem 0.125rem;
        padding: 1.2rem 1.4rem;
        font-size: 17px;
        line-height: 1.55;
        font-weight: 500;
        margin-bottom: 1rem;
        box-shadow: 0 1px 4px rgba(0, 6, 102, 0.05);
    }

    /* User Transcript Bubble */
    .stitch-user-bubble {
        background-color: #F6F3F2;
        color: #1B1C1C;
        border: 1px solid #C6C5D4;
        border-radius: 1rem 1rem 0.125rem 1rem;
        padding: 0.75rem 1rem;
        font-size: 14px;
        line-height: 1.4;
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }

    /* Large Central Pulsing Mic Animation */
    .stitch-mic-hero {
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 120px;
        height: 120px;
        margin: 0.75rem auto;
    }
    .stitch-mic-ring-outer {
        position: absolute;
        inset: 0;
        border: 3px solid #FF9933;
        border-radius: 50%;
        opacity: 0.5;
        animation: stitch-ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;
    }
    .stitch-mic-ring-inner {
        position: absolute;
        inset: 10px;
        border: 3px solid #FF9933;
        border-radius: 50%;
        opacity: 0.7;
        animation: stitch-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
    .stitch-mic-button-core {
        position: relative;
        z-index: 10;
        width: 76px;
        height: 76px;
        background-color: #000666;
        color: #FFFFFF;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 14px rgba(0, 6, 102, 0.25);
    }
    @keyframes stitch-ping {
        75%, 100% { transform: scale(1.25); opacity: 0; }
    }
    @keyframes stitch-pulse {
        50% { opacity: 0.3; }
    }

    /* Phrase Box */
    .stitch-phrase-box {
        background-color: #FFFFFF;
        border: 2px solid rgba(0, 6, 102, 0.2);
        border-radius: 0.75rem;
        padding: 1rem 1.25rem;
        margin: 0.75rem 0;
        text-align: center;
    }
    .stitch-phrase-text {
        font-size: 24px;
        font-weight: 700;
        color: #000666;
        letter-spacing: 0.16em;
    }

    /* Bento Card */
    .stitch-bento-card {
        background-color: #FFFFFF;
        border: 1px solid #C6C5D4;
        border-radius: 0.75rem;
        padding: 1rem;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    /* Chips */
    .stitch-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        background-color: #E4E2E1;
        color: #454652;
        border: 1px solid #C6C5D4;
        padding: 0.25rem 0.55rem;
        border-radius: 0.375rem;
        font-size: 12px;
        font-weight: 500;
    }

    /* Disclaimer Card */
    .stitch-disclaimer {
        background-color: #E4E2E1;
        border: 1px solid #767683;
        border-radius: 0.5rem;
        padding: 0.85rem 1.15rem;
        display: flex;
        align-items: flex-start;
        gap: 0.65rem;
        margin-top: 1rem;
    }

    /* Material Symbols font utility */
    .material-symbols-outlined {
        font-family: 'Material Symbols Outlined' !important;
        font-weight: normal !important;
        font-style: normal !important;
        font-size: 20px;
        line-height: 1;
        letter-spacing: normal;
        text-transform: none;
        display: inline-block;
        white-space: nowrap;
        word-wrap: normal;
        direction: ltr;
        -webkit-font-feature-settings: 'liga';
        -webkit-font-smoothing: antialiased;
        vertical-align: middle;
    }
</style>
"""


def inject_stitch_theme() -> None:
    """Inject Google Stitch Material 3 CSS styles into the Streamlit session."""
    st.markdown(STITCH_CSS, unsafe_allow_html=True)


def calculate_profile_completion(profile: Dict[str, Any]) -> int:
    """
    Calculate the actual dynamic profile completion percentage (0% to 100%).
    Evaluates 10 core fields with equal weighting (10% each).
    """
    if not profile:
        return 0

    evaluated_fields = [
        ("name", bool(str(profile.get("name", "")).strip())),
        ("age", bool(profile.get("age") and int(profile.get("age", 0)) > 0)),
        ("district", bool(str(profile.get("district", "")).strip())),
        ("education_level", bool(str(profile.get("education_level", "")).strip() and profile.get("education_level") != "No formal education")),
        ("current_livelihood", bool(str(profile.get("current_livelihood", "")).strip())),
        ("previous_work_experience", bool(str(profile.get("previous_work_experience", "")).strip())),
        ("skills", bool(str(profile.get("skills", "")).strip())),
        ("interests", bool(str(profile.get("interests", "")).strip())),
        ("employment_preference", bool(str(profile.get("employment_preference", "")).strip())),
        ("mobility_constraints", bool(str(profile.get("mobility_constraints", "")).strip())),
    ]

    filled_count = sum(1 for _, is_filled in evaluated_fields if is_filled)
    return int((filled_count / len(evaluated_fields)) * 100)


def render_stitch_breadcrumb(page_title: str) -> None:
    """Render Stitch breadcrumb navigation with immune chevron."""
    st.markdown(
        f"""
        <div class="stitch-breadcrumb">
            <span style="color: #000666; font-weight: 500;">Home</span>
            <span style="color: #767683; font-size: 14px; margin: 0 4px;">&rsaquo;</span>
            <span class="current">{page_title}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stitch_header(title: str, subtitle: str = "", demo_mode: bool = True) -> None:
    """Render standardized top Stitch header with title, subtitle, and Demo Mode badge."""
    badge_html = '<span class="stitch-demo-badge">Demo Mode</span>' if demo_mode else ''
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid #C6C5D4; padding-bottom: 10px; margin-bottom: 14px;">
            <div>
                <h2 style="font-size: 24px; font-weight: 700; color: #000666; margin: 0;">{title}</h2>
                {f'<p style="font-size: 14px; color: #454652; margin: 3px 0 0 0;">{subtitle}</p>' if subtitle else ''}
            </div>
            <div>
                {badge_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stitch_completion_card(completion_pct: int) -> None:
    """Render the Stitch profile completion card with dynamic percentage and progress bar."""
    st.markdown(
        f"""
        <div class="stitch-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div style="font-size: 17px; font-weight: 700; color: #000666;">Profile Completion</div>
                    <div style="font-size: 13px; color: #454652; margin-top: 3px;">
                        Complete your profile details to unlock more targeted NSQF skill pathways.
                    </div>
                </div>
                <div style="font-size: 26px; font-weight: 700; color: #000666;">
                    {completion_pct}%
                </div>
            </div>
            <div class="stitch-progress-container">
                <div class="stitch-progress-bar" style="width: {completion_pct}%;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stitch_phrase_card(phrase_str: str) -> None:
    """Render the central dynamic challenge phrase card."""
    st.markdown(
        f"""
        <div class="stitch-phrase-box">
            <div class="stitch-phrase-text">{phrase_str}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stitch_disclaimer(title: str, body: str) -> None:
    """Render standardized prototype disclaimer card."""
    st.markdown(
        f"""
        <div class="stitch-disclaimer">
            <span style="font-size: 18px; margin-top: 1px;">ℹ️</span>
            <div>
                <div style="font-weight: 700; font-size: 13px; color: #1B1C1C;">{title}</div>
                <div style="font-size: 12px; color: #454652; margin-top: 2px;">{body}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

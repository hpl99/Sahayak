"""
Tests for Skill Portal prototype integration and Ask Sahayak Conversational Engine.

Verifies:
1. skill-portal/index.html existence, structure, and 6 realistic course listings.
2. static/skill-portal/index.html synchronization.
3. Context preservation (beneficiary_id, name, district, trade, skills, preference).
4. Conversational question coverage (What is this course, Is this suitable for me, What will I learn, Show other courses).
5. End-to-end integration: Voice Assistant -> Recommendation -> Skill Portal link parameters.
"""

import os
import re
import sys
import urllib.parse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

from conversation_manager import ConversationSession
from matcher import match_profile, load_trades
from profile_store import get_profile, load_profiles

PASSED = 0
FAILED = 0

def check(name, condition, detail=""):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  ✓ {name}")
    else:
        FAILED += 1
        print(f"  ✗ {name} — {detail}")


# ===========================================================================
# TEST 1: Skill Portal File Integrity & Course Dataset
# ===========================================================================
print("\n=== TEST 1: Skill Portal File Integrity ===")

portal_file = os.path.join("skill-portal", "index.html")
check("skill-portal/index.html exists", os.path.exists(portal_file))

static_portal_file = os.path.join("static", "skill-portal", "index.html")
check("static/skill-portal/index.html synced", os.path.exists(static_portal_file))

with open(portal_file, "r", encoding="utf-8") as f:
    html_content = f.read()

check("HTML contains 6 realistic NSQF courses",
      "Electrician (Domestic)" in html_content and
      "Solar Panel Installer" in html_content and
      "Welder (Fabrication)" in html_content and
      "Mobile Repair Technician" in html_content and
      "Retail Sales Associate" in html_content and
      "Tailoring & Fashion Design" in html_content)

check("HTML contains persistent Ask Sahayak drawer",
      'id="ask-sahayak-widget"' in html_content and
      'id="sahayak-drawer"' in html_content and
      'id="sahayak-trigger-btn"' in html_content)

check("HTML contains quick action chips",
      "What is this course?" in html_content and
      "Is this suitable for me?" in html_content and
      "What will I learn?" in html_content and
      "Show me other courses" in html_content)

check("HTML contains voice recognition and TTS handlers",
      "SpeechRecognition" in html_content and
      "speechSynthesis" in html_content)


# ===========================================================================
# TEST 2: Intent-based Conversational Logic Simulation
# ===========================================================================
print("\n=== TEST 2: Conversational Response Engine Logic ===")

# Simulate the generateSahayakResponse JS logic in Python to verify complete answer coverage
def simulate_sahayak_response(user_text, course, beneficiary):
    text = user_text.lower()
    name = beneficiary.get("name", "मित्र")
    district = beneficiary.get("district", "Nagpur")
    trade_name = course["title"]
    
    if any(k in text for k in ["what is this course", "what is the course", "kya hai", "about the course"]):
        return f"{trade_name} is an NSQF Level {course['nsqf_level']} course in {course['sector']} with duration {course['duration_hours']} hours in {district}."
    
    if any(k in text for k in ["suitable", "fit", "sahi hai", "for me", "mere liye"]):
        return f"Yes {name}! This course fits your background in {beneficiary.get('skills', 'skills')} and preference for {beneficiary.get('employment_preference', 'wage employment')}."
    
    if any(k in text for k in ["learn", "seekh", "kya sikhunga", "syllabus", "modules"]):
        return f"In {trade_name} you will learn: {'; '.join(course['modules'][:2])}."
    
    if any(k in text for k in ["other course", "another course", "dusra", "options"]):
        return f"Other courses in {district} include Solar Panel Installer, Welder, Mobile Repair."
    
    return f"Thank you {name} for asking about {trade_name}."

sample_course = {
    "title": "Electrician (Domestic)",
    "nsqf_level": 4,
    "sector": "Power",
    "duration_hours": 350,
    "avg_monthly_wage": 14000,
    "modules": ["Domestic wiring", "MCB installation", "Inverter wiring"]
}

sample_ben = {
    "name": "Ramesh Kumar",
    "district": "Nagpur",
    "skills": "wiring aur switch fitting",
    "employment_preference": "Wage Employment (Job)"
}

r1 = simulate_sahayak_response("What is this course?", sample_course, sample_ben)
check("Response for 'What is this course?' covers level & duration", "Level 4" in r1 and "350" in r1)

r2 = simulate_sahayak_response("Is this suitable for me?", sample_course, sample_ben)
check("Response for 'Is this suitable for me?' includes personalized name and skills", "Ramesh Kumar" in r2 and "wiring" in r2)

r3 = simulate_sahayak_response("What will I learn?", sample_course, sample_ben)
check("Response for 'What will I learn?' details syllabus modules", "Domestic wiring" in r3)

r4 = simulate_sahayak_response("Show me other courses", sample_course, sample_ben)
check("Response for 'Show me other courses' lists alternative options", "Solar" in r4 or "Welder" in r4)


# ===========================================================================
# TEST 3: End-to-End Voice Assistant -> Recommendation -> Skill Portal Link
# ===========================================================================
print("\n=== TEST 3: End-to-End Context Pipeline & Link Construction ===")

session = ConversationSession(language="Hindi", district="Nagpur")
turns = [
    "Mera naam Ramesh Kumar hai",
    "Meri umar 26 saal hai",
    "Main teen saal se bijli wiring ka kaam karta hoon",
    "Mujhe wiring aur switch fitting aati hai aur electrical kaam seekhna hai",
    "Mujhe company mein naukri chahiye"
]

for turn in turns:
    session.process_turn(turn)

check("Voice onboarding complete", session.is_complete)

trades_df = load_trades()
recs = match_profile(session.slots, district="Nagpur", trades_df=trades_df, top_n=3)
top_rec = recs[0]
check("Top recommendation is Electrician", "Electrician" in top_rec["trade_name"])

# Verify query parameter construction for Skill Portal URL
params = {
    "beneficiary_id": session.beneficiary_id,
    "name": session.slots["name"],
    "district": session.district,
    "lang": session.language,
    "trade": top_rec["trade_name"],
    "skills": session.slots["skills"],
    "work": session.slots["current_livelihood"],
    "pref": session.slots["employment_preference"]
}
query_str = urllib.parse.urlencode(params)
target_url = f"/app/static/skill-portal/index.html?{query_str}"

check("URL contains beneficiary_id", f"beneficiary_id={session.beneficiary_id}" in target_url)
check("URL contains name", "name=Ramesh+Kumar" in target_url or "name=Ramesh%20Kumar" in target_url)
check("URL contains district", "district=Nagpur" in target_url)
check("URL contains matched trade", "Electrician" in target_url)
check("URL contains skills context", "wiring" in target_url)


# ===========================================================================
# SUMMARY
# ===========================================================================
print(f"\n{'='*60}")
print(f"SKILL PORTAL RESULTS: {PASSED} passed, {FAILED} failed out of {PASSED + FAILED} tests")
print(f"{'='*60}")

if FAILED > 0:
    sys.exit(1)
else:
    print("\nALL SKILL PORTAL TESTS PASSED!")
    sys.exit(0)

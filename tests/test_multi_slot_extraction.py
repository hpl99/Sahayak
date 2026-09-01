"""
Tests for multi-slot extraction and persistence in ConversationSession.

Verifies:
- Single-slot extraction (backward compat)
- Multi-slot extraction from one utterance
- Immediate persistence after every turn
- Dynamic question routing (skip filled slots)
- Full sequential 5-turn backward compatibility
- Reset isolation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

from conversation_manager import (
    ConversationSession,
    STEPS,
    STEP_LABELS,
    _extract_name,
    _extract_age,
    _extract_preference,
    _try_extract_name,
    _try_extract_age,
    _try_extract_work,
    _try_extract_skills,
    _try_extract_preference,
)
from profile_store import get_profile, load_profiles
from matcher import match_profile, load_trades

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
# TEST 1: Tentative extractor unit tests
# ===========================================================================

print("\n=== TEST 1: Tentative Extractors ===")

# _try_extract_name
check("name: pattern match",
      _try_extract_name("Mera naam Ramesh Kumar hai") == "Ramesh Kumar")
check("name: no pattern returns None",
      _try_extract_name("Main 26 saal ka hoon") is None)
check("name: Marathi pattern",
      _try_extract_name("Majhe naav Priya Deshpande aahe") == "Priya Deshpande")

# _try_extract_age
check("age: digit extraction",
      _try_extract_age("Meri umar 26 saal hai") == 26)
check("age: word number",
      _try_extract_age("Main pachis saal ka hoon") == 25)
check("age: no number returns None",
      _try_extract_age("Mera naam Ramesh Kumar hai") is None)

# _try_extract_work
check("work: detects kaam keyword",
      _try_extract_work("Main bijli wiring ka kaam karta hoon") is not None)
check("work: no work keywords returns None",
      _try_extract_work("Mera naam Suresh hai") is None)
check("work: detects driving",
      _try_extract_work("Main driving karta hoon") is not None)

# _try_extract_skills
check("skills: detects fitting",
      _try_extract_skills("Mujhe wiring aur switch fitting aati hai") is not None)
check("skills: detects seekhna",
      _try_extract_skills("Mujhe electrical seekhna hai") is not None)
check("skills: no skill keywords returns None",
      _try_extract_skills("Mera naam Suresh hai") is None)

# _try_extract_preference
check("preference: detects naukri",
      _try_extract_preference("Mujhe company mein naukri chahiye") == "Wage Employment (Job)")
check("preference: detects business",
      _try_extract_preference("Main apna business karna chahta hoon") == "Self Employment (Entrepreneurship / Micro-enterprise)")
check("preference: no preference keywords returns None",
      _try_extract_preference("Mera naam Suresh hai") is None)


# ===========================================================================
# TEST 2: Multi-slot extraction from a single utterance
# ===========================================================================

print("\n=== TEST 2: Multi-Slot Extraction (name + age in one utterance) ===")

session = ConversationSession(language="Hindi", district="Nagpur")
sid = session.beneficiary_id

# First question is "name". User answers with name AND age.
q, done = session.process_turn("Mera naam Priya hai aur meri umar 22 saal hai")

check("name extracted", session.slots["name"] == "Priya",
      f"got {session.slots['name']!r}")
check("age extracted from same utterance", session.slots["age"] == 22,
      f"got {session.slots['age']!r}")
check("2 slots filled", session._filled_count() == 2,
      f"got {session._filled_count()}")
check("next question is work (skips age)", session.current_step == "work",
      f"got {session.current_step!r}")
check("not complete yet", not done)
check("progress is 40%", session.get_progress() == 0.4,
      f"got {session.get_progress()}")


# ===========================================================================
# TEST 3: Multi-slot extraction (work + skills + preference)
# ===========================================================================

print("\n=== TEST 3: Multi-Slot Extraction (work + skills + preference) ===")

q, done = session.process_turn(
    "Main teen saal se bijli wiring ka kaam karta hoon aur switch fitting aati hai "
    "aur mujhe company mein naukri chahiye"
)

check("work slot filled", bool(session.slots["current_livelihood"]),
      f"got {session.slots['current_livelihood']!r}")
check("skills slot filled", bool(session.slots["skills"]),
      f"got {session.slots['skills']!r}")
check("preference slot filled", bool(session.slots["employment_preference"]),
      f"got {session.slots['employment_preference']!r}")
check("conversation complete after 2 turns", done,
      f"is_complete={session.is_complete}")
check("all 5 slots filled", session._filled_count() == 5,
      f"got {session._filled_count()}")


# ===========================================================================
# TEST 4: Immediate persistence after every turn
# ===========================================================================

print("\n=== TEST 4: Immediate Persistence ===")

session2 = ConversationSession(language="Hindi", district="Nagpur")
sid2 = session2.beneficiary_id

# Only answer with name
session2.process_turn("Mera naam Asha hai")

# Check profile_store immediately
stored = get_profile(sid2)
check("profile exists after 1 turn", stored is not None)
check("name persisted immediately", stored.get("name") == "Asha",
      f"got {stored.get('name')!r}")


# ===========================================================================
# TEST 5: Dynamic question skip
# ===========================================================================

print("\n=== TEST 5: Dynamic Question Routing ===")

# Continue session2 — name is filled, age is not
check("next question is for age", session2.current_step == "age")

# Answer with age + work in one go
session2.process_turn("Meri umar 30 saal hai aur main driving ka kaam karta hoon")

check("age filled", session2.slots["age"] == 30, f"got {session2.slots['age']!r}")
check("work filled from same utterance", bool(session2.slots["current_livelihood"]),
      f"got {session2.slots['current_livelihood']!r}")
check("next question skips to skills", session2.current_step == "skills",
      f"got {session2.current_step!r}")
check("3 of 5 filled", session2._filled_count() == 3,
      f"got {session2._filled_count()}")


# ===========================================================================
# TEST 6: Full sequential 5-turn (backward compatibility)
# ===========================================================================

print("\n=== TEST 6: Sequential 5-Turn Backward Compatibility ===")

seq = ConversationSession(language="Hindi", district="Nagpur")
seq_id = seq.beneficiary_id

turns = [
    ("Mera naam Ramesh Kumar hai", "name", "Ramesh Kumar"),
    ("Meri umar 26 saal hai", "age", 26),
    ("Main teen saal se bijli wiring ka kaam karta hoon", "current_livelihood",
     "Main teen saal se bijli wiring ka kaam karta hoon"),
    ("Mujhe wiring aur switch fitting aati hai aur electrical kaam seekhna hai", "skills",
     "Mujhe wiring aur switch fitting aati hai aur electrical kaam seekhna hai"),
    ("Mujhe company mein naukri chahiye", "employment_preference", "Wage Employment (Job)"),
]

for i, (utt, slot, expected) in enumerate(turns):
    q, done = seq.process_turn(utt)
    actual = seq.slots.get(slot)
    check(f"turn {i+1}: {slot} = {expected!r}",
          actual == expected, f"got {actual!r}")

check("session complete after 5 turns", seq.is_complete)
check("history has 5 entries", len(seq.history) == 5,
      f"got {len(seq.history)}")

# Verify profile persistence
sp = get_profile(seq_id)
check("profile persisted", sp is not None)
check("profile name correct", sp["name"] == "Ramesh Kumar")

# Verify matcher still works
trades_df = load_trades()
recs = match_profile(seq.slots, district="Nagpur", trades_df=trades_df)
check("matcher returns recommendations", len(recs) > 0)
check("top match is electrical-related",
      "Electrician" in recs[0]["trade_name"] or "Solar" in recs[0]["trade_name"],
      f"got {recs[0]['trade_name']}")


# ===========================================================================
# TEST 7: Reset isolation
# ===========================================================================

print("\n=== TEST 7: Reset Isolation ===")

old_profiles = len(load_profiles())
new_session = ConversationSession(language="Hindi", district="Nagpur")
check("new session gets new ID", new_session.beneficiary_id != seq_id)
check("new session starts empty", new_session._filled_count() == 0)
check("new session not complete", not new_session.is_complete)
check("old profile preserved", get_profile(seq_id) is not None)


# ===========================================================================
# TEST 8: Name extraction with noise filtering
# ===========================================================================

print("\n=== TEST 8: Name Extraction with Noise Words ===")

ns = ConversationSession(language="Hindi", district="Nagpur")
ns.process_turn("Mera naam Raj hai aur meri umar 30 saal hai")
check("name extracted without noise", ns.slots["name"] == "Raj",
      f"got {ns.slots['name']!r}")
check("age also extracted", ns.slots["age"] == 30,
      f"got {ns.slots['age']!r}")


# ===========================================================================
# SUMMARY
# ===========================================================================

print(f"\n{'='*60}")
print(f"RESULTS: {PASSED} passed, {FAILED} failed out of {PASSED + FAILED} tests")
print(f"{'='*60}")

if FAILED > 0:
    sys.exit(1)
else:
    print("\nALL TESTS PASSED!")
    sys.exit(0)

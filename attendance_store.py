"""
Attendance Integrity verification and storage for Voice for Livelihood.

Generates random challenge phrases per check-in, uses the existing ASR model
to transcribe spoken trainee audio, compares expected vs transcribed phrases
to prevent static replay attacks, and stores check-in records in data/attendance.json.

NOTE: This is a demo/prototype feature. Voice identity verification (biometrics)
is not implemented.
"""

import json
import os
import random
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

DATA_DIR = "data"
ATTENDANCE_FILE = os.path.join(DATA_DIR, "attendance.json")

NUMBER_WORDS = {
    0: {"zero", "shunya", "0", "शून्य", "झिरो"},
    1: {"one", "ek", "1", "एक", "वन"},
    2: {"two", "do", "don", "2", "दो", "दोन", "टू"},
    3: {"three", "teen", "tin", "3", "तीन", "थ्री"},
    4: {"four", "char", "4", "चार", "फोर"},
    5: {"five", "paanch", "panch", "5", "पाच", "पाँच", "फाइव"},
    6: {"six", "chhah", "saha", "6", "छह", "सहा", "सिक्स"},
    7: {"seven", "saat", "sat", "7", "सात", "सेवन"},
    8: {"eight", "aath", "ath", "8", "आठ", "एट"},
    9: {"nine", "nau", "nav", "9", "नौ", "नऊ", "नाइन"},
}

DIGIT_NAMES_EN = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
DIGIT_NAMES_HI = ["शून्य", "एक", "दो", "तीन", "चार", "पाँच", "छह", "सात", "आठ", "नौ"]


def _ensure_storage() -> None:
    """Ensure data directory and attendance.json exist."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(ATTENDANCE_FILE):
        with open(ATTENDANCE_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)


def load_attendance() -> List[Dict[str, Any]]:
    """Load all attendance records."""
    _ensure_storage()
    try:
        with open(ATTENDANCE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, OSError):
        return []


def save_attendance_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Save an attendance check-in record."""
    _ensure_storage()
    records = load_attendance()
    if not record.get("record_id"):
        next_num = len(records) + 1
        record["record_id"] = f"ATT-{datetime.now().year}-{next_num:04d}"
    if not record.get("timestamp"):
        record["timestamp"] = datetime.now().isoformat()

    records.append(record)
    with open(ATTENDANCE_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    return record


def generate_challenge_phrase(length: int = 4) -> Dict[str, Any]:
    """
    Generate a random dynamic multi-digit challenge phrase for attendance check-in.
    Example: 'Four Seven Two Nine'
    """
    digits = [random.randint(1, 9) for _ in range(length)]
    words_en = [DIGIT_NAMES_EN[d] for d in digits]
    words_hi = [DIGIT_NAMES_HI[d] for d in digits]
    digits_str = " ".join(str(d) for d in digits)
    phrase_en = " ".join(words_en)
    phrase_hi = " ".join(words_hi)

    return {
        "digits": digits,
        "digits_str": digits_str,
        "phrase_en": phrase_en,
        "phrase_hi": phrase_hi,
        "expected_phrase": f"{phrase_en} ({digits_str})",
    }


def verify_phrase_match(
    expected_digits: List[int],
    transcript: str,
) -> Tuple[str, bool, float, str]:
    """
    Compare expected challenge phrase digits against transcribed audio.

    Returns:
        (status ['Pass', 'Fail'], flagged [True, False], match_score [0.0-1.0], reason_text)
    """
    if not transcript or not transcript.strip():
        return "Fail", True, 0.0, "No speech detected in recorded audio"

    # Clean text while preserving Indic matras and Unicode words
    clean_text = transcript.lower()
    for punc in [".", ",", "!", "?", ";", ":", "-", "_", "(", ")", "[", "]", "{", "}", "\"", "'", "/", "\\", "|"]:
        clean_text = clean_text.replace(punc, " ")
    
    tokens = set(clean_text.split())

    # Check for direct digits in transcript string
    found_digits = []
    digit_chars = re.findall(r"\d", clean_text)
    for dc in digit_chars:
        try:
            found_digits.append(int(dc))
        except ValueError:
            pass

    # Check for word tokens
    matched_expected = 0
    total_expected = len(expected_digits)

    for d in expected_digits:
        aliases = NUMBER_WORDS.get(d, set())
        # Check if digit token or alias exists in tokens or in raw text
        if d in found_digits:
            matched_expected += 1
        elif any(alias in tokens for alias in aliases):
            matched_expected += 1
        elif any(alias in clean_text for alias in aliases):
            matched_expected += 1

    match_score = matched_expected / total_expected if total_expected > 0 else 0.0

    if match_score >= 0.75:
        return "Pass", False, match_score, f"Matched {matched_expected}/{total_expected} challenge elements"
    elif match_score >= 0.40:
        return "Pass", True, match_score, f"Partial match ({matched_expected}/{total_expected}) — Flagged for review"
    else:
        return "Fail", True, match_score, f"Low match ({matched_expected}/{total_expected} elements) — Phrase mismatch"

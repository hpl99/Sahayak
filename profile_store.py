"""
Local persistent profile store for Voice for Livelihood beneficiaries.

Stores beneficiary profiles in data/profiles.json using standard JSON.
No external database or cloud dependency required.
Designed for both direct UI usage and future conversational chatbot slot accumulation.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

DATA_DIR = "data"
PROFILES_FILE = os.path.join(DATA_DIR, "profiles.json")


def _ensure_storage() -> None:
    """Ensure data directory and profiles.json exist."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PROFILES_FILE):
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)


def generate_beneficiary_id() -> str:
    """Generate a unique sequential beneficiary ID (e.g., BEN-2026-001)."""
    profiles = load_profiles()
    current_year = datetime.now().year
    prefix = f"BEN-{current_year}-"

    existing_nums = []
    for p in profiles:
        b_id = str(p.get("beneficiary_id", ""))
        if b_id.startswith(prefix):
            suffix = b_id[len(prefix):]
            if suffix.isdigit():
                existing_nums.append(int(suffix))

    next_num = max(existing_nums, default=0) + 1
    return f"{prefix}{next_num:03d}"


def load_profiles() -> List[Dict[str, Any]]:
    """Load all beneficiary profiles from local JSON storage."""
    _ensure_storage()
    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, OSError):
        return []


def get_profile(beneficiary_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single profile by beneficiary ID."""
    if not beneficiary_id:
        return None
    profiles = load_profiles()
    for p in profiles:
        if p.get("beneficiary_id") == beneficiary_id:
            return p
    return None


def list_profiles() -> List[Dict[str, Any]]:
    """Return list of all profiles."""
    return load_profiles()


def save_profile(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save or update a beneficiary profile.

    If beneficiary_id is missing or new, creates a new entry.
    If beneficiary_id exists, updates the existing entry in place.
    """
    _ensure_storage()
    profiles = load_profiles()

    beneficiary_id = profile_data.get("beneficiary_id")
    if not beneficiary_id:
        beneficiary_id = generate_beneficiary_id()
        profile_data["beneficiary_id"] = beneficiary_id

    if not profile_data.get("created_at"):
        profile_data["created_at"] = datetime.now().isoformat()

    # Ensure complete schema definition
    default_schema = {
        "beneficiary_id": beneficiary_id,
        "name": "",
        "age": 25,
        "gender": "Other",
        "district": "Nagpur",
        "education_level": "10th Pass",
        "family_occupation": "",
        "current_livelihood": "",
        "previous_work_experience": "",
        "skills": "",
        "interests": "",
        "mobility_constraints": "Local only (within district)",
        "employment_preference": "Wage Employment (Job)",
        "language": "Hindi",
        "training_status": "Not Started",
        "training_start_date": None,
        "training_completion_date": None,
        "recommended_trade": None,
        "created_at": profile_data["created_at"],
    }

    merged = {**default_schema, **profile_data}

    # Update or insert
    updated = False
    for i, p in enumerate(profiles):
        if p.get("beneficiary_id") == beneficiary_id:
            profiles[i] = merged
            updated = True
            break

    if not updated:
        profiles.append(merged)

    with open(PROFILES_FILE, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)

    return merged


def update_profile_slots(beneficiary_id: str, slots: Dict[str, Any]) -> Dict[str, Any]:
    """
    Incrementally update extracted conversational slots for a beneficiary.
    Allows future conversational managers to write turn-by-turn slots.
    """
    profile = get_profile(beneficiary_id) or {"beneficiary_id": beneficiary_id}
    profile.update(slots)
    return save_profile(profile)

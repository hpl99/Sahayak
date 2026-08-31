"""
Training follow-up store for Voice for Livelihood.

Manages post-training 30-day, 60-day, and 180-day milestone check-ins,
supports Demo Mode time-scaling (30s / 60s / 180s), and stores outcome responses
in data/followups.json.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from profile_store import get_profile, save_profile

DATA_DIR = "data"
FOLLOWUPS_FILE = os.path.join(DATA_DIR, "followups.json")


def _ensure_storage() -> None:
    """Ensure data directory and followups.json exist."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(FOLLOWUPS_FILE):
        with open(FOLLOWUPS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)


def load_followups() -> List[Dict[str, Any]]:
    """Load all follow-up records."""
    _ensure_storage()
    try:
        with open(FOLLOWUPS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, OSError):
        return []


def save_followups_data(records: List[Dict[str, Any]]) -> None:
    """Save raw list of follow-up records to JSON."""
    _ensure_storage()
    with open(FOLLOWUPS_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def get_beneficiary_followups(beneficiary_id: str) -> List[Dict[str, Any]]:
    """Get all milestone records for a specific beneficiary."""
    records = load_followups()
    return [r for r in records if r.get("beneficiary_id") == beneficiary_id]


def mark_training_complete(
    beneficiary_id: str,
    trade_name: Optional[str] = None,
    completion_time: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """
    Mark a beneficiary's training as complete and initialize 30/60/180-day follow-up milestones.

    Also updates the profile's training_status and training_completion_date.
    """
    if completion_time is None:
        completion_time = datetime.now()

    comp_iso = completion_time.isoformat()

    # 1. Update Profile
    profile = get_profile(beneficiary_id)
    if profile:
        profile["training_status"] = "Completed"
        profile["training_completion_date"] = comp_iso
        if trade_name:
            profile["recommended_trade"] = trade_name
        save_profile(profile)

    # 2. Generate Milestones (30 days, 60 days, 180 days)
    # In Demo Mode: 30s, 60s, 180s
    milestones_def = [
        ("30-day", 30, 30),
        ("60-day", 60, 60),
        ("180-day", 180, 180),
    ]

    all_records = load_followups()
    # Remove any existing pending records for this beneficiary to avoid duplicates
    existing_unanswered = [
        r for r in all_records
        if not (r.get("beneficiary_id") == beneficiary_id and r.get("status") == "Pending")
    ]

    new_milestones = []
    trade = trade_name or (profile.get("recommended_trade") if profile else "General Vocational")

    for name, real_days, demo_secs in milestones_def:
        real_due = (completion_time + timedelta(days=real_days)).isoformat()
        demo_due = (completion_time + timedelta(seconds=demo_secs)).isoformat()
        clean_bid = beneficiary_id.replace("-", "")

        record = {
            "followup_id": f"FOL-{clean_bid}-{name}",
            "beneficiary_id": beneficiary_id,
            "trade_name": trade,
            "milestone": name,
            "milestone_days": real_days,
            "demo_seconds": demo_secs,
            "completion_date": comp_iso,
            "due_date_real": real_due,
            "due_date_demo": demo_due,
            "status": "Pending",
            "survey_response": None,
        }
        new_milestones.append(record)
        existing_unanswered.append(record)

    save_followups_data(existing_unanswered)
    return new_milestones


def record_survey_response(
    followup_id: str,
    response: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Record answers to the 4 follow-up questions:
    1. is_working ("Yes" / "No")
    2. work_related_to_training ("Yes" / "No" / "Somewhat")
    3. monthly_income_inr (int or str)
    4. wants_new_recommendation ("Yes" / "No")
    """
    records = load_followups()
    updated_record = None

    for r in records:
        if r.get("followup_id") == followup_id:
            response["submitted_at"] = datetime.now().isoformat()
            r["survey_response"] = response
            r["status"] = "Completed"
            updated_record = r
            break

    if updated_record:
        save_followups_data(records)

    return updated_record


def get_milestone_timing(record: Dict[str, Any], demo_mode: bool = False) -> Dict[str, Any]:
    """
    Calculate time status (Due, Elapsed, Remaining seconds/days) for a milestone.
    """
    comp_str = record.get("completion_date")
    if not comp_str:
        return {"is_due": True, "remaining_seconds": 0, "status_label": "Ready"}

    try:
        comp_time = datetime.fromisoformat(comp_str)
    except ValueError:
        comp_time = datetime.now()

    now = datetime.now()
    elapsed_seconds = (now - comp_time).total_seconds()

    if record.get("status") == "Completed":
        return {
            "is_due": True,
            "is_completed": True,
            "remaining_seconds": 0,
            "status_label": "Completed (Survey Submitted)",
        }

    if demo_mode:
        target_seconds = record.get("demo_seconds", 30)
        remaining = target_seconds - elapsed_seconds
        if remaining <= 0:
            return {
                "is_due": True,
                "is_completed": False,
                "remaining_seconds": 0,
                "status_label": "🔔 Due Now (Demo Mode: 30s/60s/180s)",
            }
        else:
            return {
                "is_due": False,
                "is_completed": False,
                "remaining_seconds": int(remaining),
                "status_label": f"⏳ Scheduled (Demo: {int(remaining)}s remaining)",
            }
    else:
        target_days = record.get("milestone_days", 30)
        due_date = comp_time + timedelta(days=target_days)
        remaining_days = (due_date - now).days
        if now >= due_date:
            return {
                "is_due": True,
                "is_completed": False,
                "remaining_seconds": 0,
                "status_label": "🔔 Due Now",
            }
        else:
            return {
                "is_due": False,
                "is_completed": False,
                "remaining_seconds": max(0, int((due_date - now).total_seconds())),
                "status_label": f"⏳ Scheduled ({remaining_days} days remaining)",
            }

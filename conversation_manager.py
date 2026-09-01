"""
Conversation Manager for Voice for Livelihood.

Orchestrates multi-turn, voice-first progressive profile collection:
1. Name
2. Age
3. Current Livelihood & Work Experience
4. Skills & Learning Interests
5. Employment Preference (Wage vs Self-Employment)

Uses deterministic state machine, multilingual question templates, and connects directly
to profile_store.py, matcher.py, and speech.py.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from profile_store import get_profile, save_profile, update_profile_slots, generate_beneficiary_id

STEPS = [
    "name",
    "age",
    "work",
    "skills",
    "preference",
]

STEP_LABELS = {
    "name": "Full Name",
    "age": "Age",
    "work": "Current Work & Experience",
    "skills": "Skills & Interests",
    "preference": "Employment Preference",
}

# Multilingual Question Templates
QUESTIONS = {
    "Hindi": {
        "name": "नमस्ते! आपका शुभ नाम क्या है?",
        "age": "धन्यवाद {name}। आपकी उम्र कितनी है?",
        "work": "आप अभी क्या काम करते हैं, और पहले किस काम का अनुभव रहा है?",
        "skills": "आपको क्या हुनर या काम आता है, और आगे क्या नया सीखना चाहते हैं?",
        "preference": "आप नौकरी करना पसंद करेंगे या अपनी खुद की दुकान या व्यवसाय शुरू करना चाहते हैं?",
        "complete": "धन्यवाद {name}! आपकी पूरी जानकारी दर्ज कर ली गई है। अब आपके लिए उपयुक्त एनएसक्यूएफ कोर्स खोजे जा रहे हैं।",
    },
    "Marathi": {
        "name": "नमस्कार! आपले शुभ नाव काय आहे?",
        "age": "धन्यवाद {name}। आपले वय किती आहे?",
        "work": "तुम्ही सध्या काय काम करता, आणि आधी कोणता कामाचा अनुभव आहे?",
        "skills": "तुमच्याकडे कोणते कौशल्य किंवा हुनर आहे, आणि पुढे काय शिकायला आवडेल?",
        "preference": "तुम्हाला नोकरी करायची आहे की स्वतःचा व्यवसाय किंवा दुकान सुरू करायचे आहे?",
        "complete": "धन्यवाद {name}! आपली सर्व माहिती नोंदवली गेली आहे. आपल्यासाठी योग्य एनएसक्यूएफ अभ्यासक्रम शोधले जात आहेत.",
    },
    "Telugu": {
        "name": "నమస్కారం! మీ పేరు ఏమిటి?",
        "age": "ధన్యవాదాలు {name}. మీ వయస్సు ఎంత?",
        "work": "మీరు ప్రస్తుతం ఏమి పని చేస్తున్నారు, మరియు గతంలో ఏమి పని చేశారు?",
        "skills": "మీకు ఎలాంటి నైపుణ్యాలు ఉన్నాయి, మరియు ఏమి నేర్చుకోవాలనుకుంటున్నారు?",
        "preference": "మీరు ఉద్యోగం చేయాలనుకుంటున్నారా లేదా స్వంత వ్యాపారం ప్రారంభించాలనుకుంటున్నారా?",
        "complete": "ధన్యవాదాలు {name}! మీ వివరాలు నమోదు చేయబడ్డాయి. మీ కోసం అనువైన కోర్సులు వెతుకుతున్నాము.",
    },
    "Tamil": {
        "name": "வணக்கம்! உங்கள் பெயர் என்ன?",
        "age": "நன்றி {name}. உங்கள் வயது என்ன?",
        "work": "நீங்கள் தற்போது என்ன வேலை செய்கிறீர்கள், மற்றும் முன்பு என்ன அனுபவம் உள்ளது?",
        "skills": "உங்களுக்கு என்ன திறன்கள் தெரியும், மேலும் என்ன கற்க விரும்புகிறீர்கள்?",
        "preference": "நீங்கள் வேலை செய்ய விரும்புகிறீர்களா அல்லது சொந்த தொழில் தொடங்க விரும்புகிறீர்களா?",
        "complete": "நன்றி {name}! உங்கள் தகவல்கள் பதிவு செய்யப்பட்டன. உங்களுக்கான பயிற்சிகள் கண்டறியப்படுகின்றன.",
    },
    "Bengali": {
        "name": "নমস্কার! আপনার নাম কি?",
        "age": "ধন্যবাদ {name}। আপনার বয়স কত?",
        "work": "আপনি বর্তমানে কি কাজ করেন, এবং আগে কি কাজের অভিজ্ঞতা আছে?",
        "skills": "আপনার কি কি দক্ষতা আছে, এবং ভবিষ্যতে কি শিখতে চান?",
        "preference": "আপনি কি চাকরি করতে চান নাকি নিজের ব্যবসা শুরু করতে চান?",
        "complete": "ধন্যবাদ {name}! আপনার তথ্য সংরক্ষিত হয়েছে। আপনার জন্য উপযুক্ত কোর্স খোঁজা হচ্ছে।",
    },
    "Gujarati": {
        "name": "નમસ્તે! તમારું શુભ નામ શું છે?",
        "age": "આભાર {name}. તમારી ઉંમર કેટલી છે?",
        "work": "તમે હાલમાં શું કામ કરો છો, અને પહેલાં કયો કામનો અનુભવ છે?",
        "skills": "તમારામાં કઈ આવડત કે કૌશલ્ય છે, અને આગળ શું શીખવા માંગો છો?",
        "preference": "તમે નોકરી કરવા માંગો છો કે તમારો પોતાનો વ્યવસાય શરૂ કરવા માંગો છો?",
        "complete": "આભાર {name}! તમારી બધી વિગતો નોંધી લેવામાં આવી છે. તમારા માટે યોગ્ય અભ્યાસક્રમો શોધાઈ રહ્યા છે.",
    },
}

# Number words for spoken age extraction
AGE_WORDS = {
    "athara": 18, "unnis": 19, "bees": 20, "ikkis": 21, "baais": 22, "teis": 23,
    "chaubees": 24, "pachis": 25, "chhabis": 26, "sattais": 27, "atthais": 28,
    "unatis": 29, "tees": 30, "ikatis": 31, "battis": 32, "tentis": 33, "chauntis": 34,
    "paintis": 35, "chhattis": 36, "saintis": 37, "adhtis": 38, "untalis": 39, "chalis": 40,
    "paintalis": 45, "pachas": 50, " बचपन": 55, "saath": 60,
    "eighteen": 18, "nineteen": 19, "twenty": 20, "twenty one": 21, "twenty two": 22,
    "twenty three": 23, "twenty four": 24, "twenty five": 25, "twenty six": 26,
    "twenty seven": 27, "twenty eight": 28, "twenty nine": 29, "thirty": 30,
    "thirty five": 35, "forty": 40, "forty five": 45, "fifty": 50,
}


# ---------------------------------------------------------------------------
# NAME PATTERNS (shared by both extract and try_extract)
# ---------------------------------------------------------------------------

_NAME_PATTERNS = [
    r"(?:mera|mara|hamara)\s+naam\s+(.*?)\s+hai",
    r"(?:mera|mara|hamara)\s+naam\s+(.*?)$",
    r"naam\s+(.*?)\s+hai",
    r"majhe\s+naav\s+(.*?)\s+aahe",
    r"majhe\s+naav\s+(.*?)$",
    r"my\s+name\s+is\s+(.*?)$",
    r"i\s+am\s+(.*?)$",
    r"main\s+([A-Za-z\u0900-\u097F]+(?:\s+[A-Za-z\u0900-\u097F]+)*)\s+hoon$",
    r"naa\s+peru\s+(.*?)$",
    r"en\s+peyar\s+(.*?)$",
    r"aamar\s+naam\s+(.*?)$",
    r"maru\s+naam\s+(.*?)$",
]


def _match_name_pattern(text: str):
    """Try to match an explicit name pattern. Returns cleaned name or None."""
    for pat in _NAME_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE)
        if m and m.group(1).strip():
            candidate = m.group(1).strip()
            candidate = re.sub(r"[^\w\s]", "", candidate, flags=re.UNICODE).strip()
            # Remove trailing noise words that are clearly not part of a name
            noise_tail = re.compile(
                r"\s+(?:aur|or|hai|hoon|hun|ka|ki|ke|se|mein|main|meri|mera|umar|saal|years?)\b.*$",
                re.IGNORECASE,
            )
            candidate = noise_tail.sub("", candidate).strip()
            if candidate:
                return candidate.title()
    return None


def _extract_name(transcript: str) -> str:
    """Extract name entity from spoken transcript (always returns a value)."""
    text = transcript.strip()
    result = _match_name_pattern(text)
    if result:
        return result

    # Fallback: use cleaned transcript as the name (up to 3 words)
    clean = re.sub(r"[^\w\s]", "", text, flags=re.UNICODE).strip()
    words = clean.split()
    if words:
        return " ".join(words[:3]).title()
    return "Beneficiary"


def _extract_age(transcript: str) -> int:
    """Extract age integer from spoken transcript (always returns a value)."""
    text = transcript.lower()
    digits = re.findall(r"\b\d{1,2}\b", text)
    if digits:
        val = int(digits[0])
        if 14 <= val <= 85:
            return val
    for word, val in AGE_WORDS.items():
        if word in text:
            return val
    return 25  # Sensible default


def _extract_preference(transcript: str) -> str:
    """Extract wage vs self-employment preference (always returns a value)."""
    text = transcript.lower()
    self_keywords = [
        "apna", "khud", "dukan", "dukaan", "business", "vyavsay", "dhandha",
        "self", "entrepreneur", "boutique", "parlour", "shop", "own", "svatah"
    ]
    for kw in self_keywords:
        if kw in text:
            return "Self Employment (Entrepreneurship / Micro-enterprise)"
    return "Wage Employment (Job)"


# ---------------------------------------------------------------------------
# TENTATIVE (confidence-gated) extractors for multi-slot extraction.
# These return None when not confident, so they never produce false positives.
# ---------------------------------------------------------------------------

def _try_extract_name(transcript: str):
    """Return name only if an explicit pattern matches. None otherwise."""
    return _match_name_pattern(transcript.strip())


def _try_extract_age(transcript: str):
    """Return age only if an explicit number is found. None otherwise."""
    text = transcript.lower()
    digits = re.findall(r"\b\d{1,2}\b", text)
    if digits:
        val = int(digits[0])
        if 14 <= val <= 85:
            return val
    for word, val in AGE_WORDS.items():
        if word in text:
            return val
    return None


# Keyword signals for work / livelihood detection
_WORK_KEYWORDS = {
    "kaam", "karta", "karti", "karte", "kam", "kaamgaar",
    "wiring", "driving", "farming", "kheti", "mazdoori", "labour",
    "mechanic", "plumbing", "welding", "electrician", "mason",
    "painting", "carpenter", "carpentry", "construction", "factory",
    "hotel", "delivery", "rickshaw", "auto", "truck", "tempo",
    "dukaan", "shop", "selling", "vendor", "hawker",
    "experience", "anubhav",
    "bijli", "solar", "tailoring", "silai", "bunai",
    "salon", "barber", "cooking", "helper",
    "work", "working", "job", "employed",
}


def _try_extract_work(transcript: str):
    """Return transcript as work description if work-related keywords found. None otherwise."""
    text = transcript.strip()
    tokens = set(re.sub(r"[^\w\s]", " ", text.lower(), flags=re.UNICODE).split())
    if tokens & _WORK_KEYWORDS:
        return text
    return None


# Keyword signals for skills / learning interest detection
_SKILL_KEYWORDS = {
    "aati", "aata", "seekhna", "sikhna", "learn", "learning",
    "fitting", "sewing", "stitching", "embroidery", "design",
    "repair", "maintenance", "training", "course", "certification",
    "computer", "digital", "mobile", "phone",
    "beautician", "beauty", "parlour", "makeup",
    "skill", "skills", "hunar", "hath",
    "cooking", "baking", "food", "processing",
    "wiring", "plumbing", "welding", "carpentry",
    "interest", "interested", "pasand", "chahta", "chahti",
    "electrical", "solar", "panel", "installation",
}


def _try_extract_skills(transcript: str):
    """Return transcript as skills description if skill-related keywords found. None otherwise."""
    text = transcript.strip()
    tokens = set(re.sub(r"[^\w\s]", " ", text.lower(), flags=re.UNICODE).split())
    if tokens & _SKILL_KEYWORDS:
        return text
    return None


# Keyword signals for employment preference detection
_SELF_EMP_KEYWORDS = {
    "apna", "khud", "dukan", "dukaan", "business", "vyavsay", "dhandha",
    "self", "entrepreneur", "boutique", "parlour", "shop", "own", "svatah",
    "udyog", "startup",
}
_WAGE_EMP_KEYWORDS = {
    "naukri", "job", "company", "factory", "employ", "office",
    "salary", "tankhah", "mazdoori", "wages", "wage",
    "sarkari", "private", "government",
}


def _try_extract_preference(transcript: str):
    """Return preference only if explicit keywords are found. None otherwise."""
    text = transcript.lower()
    tokens = set(re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE).split())
    if tokens & _SELF_EMP_KEYWORDS:
        return "Self Employment (Entrepreneurship / Micro-enterprise)"
    if tokens & _WAGE_EMP_KEYWORDS:
        return "Wage Employment (Job)"
    return None


class ConversationSession:
    """
    State machine session tracking the progressive voice onboarding conversation.

    Supports multi-slot extraction: each utterance may fill multiple profile
    fields at once.  The next question is dynamically chosen from whichever
    slot is still missing, rather than blindly following a fixed sequence.
    Profile is persisted after every turn.
    """

    # The five onboarding slot keys in default question order
    _SLOT_MAP = {
        "name": "name",
        "age": "age",
        "work": "current_livelihood",
        "skills": "skills",
        "preference": "employment_preference",
    }

    def __init__(
        self,
        beneficiary_id: Optional[str] = None,
        language: str = "Hindi",
        district: str = "Nagpur",
        existing_profile: Optional[Dict[str, Any]] = None,
    ):
        self.beneficiary_id = beneficiary_id or generate_beneficiary_id()
        self.language = language if language in QUESTIONS else "Hindi"
        self.district = district
        self.history: List[Dict[str, str]] = []

        # Check if profile already exists in storage or was provided
        saved = existing_profile or get_profile(self.beneficiary_id)
        if saved:
            self.slots: Dict[str, Any] = {
                "beneficiary_id": self.beneficiary_id,
                "language": saved.get("language", self.language),
                "district": saved.get("district", self.district),
                "name": saved.get("name", ""),
                "age": saved.get("age", ""),
                "current_livelihood": saved.get("current_livelihood", ""),
                "previous_work_experience": saved.get("previous_work_experience", ""),
                "skills": saved.get("skills", ""),
                "interests": saved.get("interests", ""),
                "employment_preference": saved.get("employment_preference", ""),
                "education_level": saved.get("education_level", "10th Pass"),
                "mobility_constraints": saved.get("mobility_constraints", "Local only (within district)"),
            }
            self.language = self.slots["language"] if self.slots["language"] in QUESTIONS else "Hindi"
            self.district = self.slots["district"]
        else:
            self.slots = {
                "beneficiary_id": self.beneficiary_id,
                "language": self.language,
                "district": self.district,
                "name": "",
                "age": "",
                "current_livelihood": "",
                "previous_work_experience": "",
                "skills": "",
                "interests": "",
                "employment_preference": "",
                "education_level": "10th Pass",
                "mobility_constraints": "Local only (within district)",
            }

        # Derive dynamic state from actual slot contents
        self._recompute_state()

    # ------------------------------------------------------------------
    # Slot-filled checks
    # ------------------------------------------------------------------

    def _slot_filled(self, step_key: str) -> bool:
        """Check whether a specific onboarding slot is meaningfully filled."""
        if step_key == "name":
            return bool(self.slots.get("name"))
        elif step_key == "age":
            val = self.slots.get("age")
            return val is not None and val != "" and val != 0
        elif step_key == "work":
            return bool(self.slots.get("current_livelihood"))
        elif step_key == "skills":
            return bool(self.slots.get("skills"))
        elif step_key == "preference":
            return bool(self.slots.get("employment_preference"))
        return False

    def _filled_count(self) -> int:
        """Count how many of the 5 onboarding slots are filled."""
        return sum(1 for s in STEPS if self._slot_filled(s))

    def _first_missing_step(self) -> Optional[str]:
        """Return the first STEPS entry whose slot is not yet filled, or None."""
        for s in STEPS:
            if not self._slot_filled(s):
                return s
        return None

    def _recompute_state(self):
        """Recompute current_step_idx and is_complete from slot contents."""
        self.current_step_idx = self._filled_count()
        self.is_complete = self.current_step_idx >= len(STEPS)

    # ------------------------------------------------------------------
    # Dynamic step / question
    # ------------------------------------------------------------------

    @property
    def current_step(self) -> str:
        missing = self._first_missing_step()
        return missing if missing else "complete"

    def get_current_question(self) -> str:
        """Get the localized question text for the current (next missing) step."""
        q_dict = QUESTIONS.get(self.language, QUESTIONS["Hindi"])
        step = self.current_step
        if step == "complete":
            name = self.slots.get("name") or "Beneficiary"
            return q_dict["complete"].format(name=name)
        elif step == "age":
            name = self.slots.get("name") or "Beneficiary"
            return q_dict["age"].format(name=name)
        else:
            return q_dict.get(step, q_dict["name"])

    # ------------------------------------------------------------------
    # Multi-slot turn processing
    # ------------------------------------------------------------------

    def process_turn(self, transcript: str) -> Tuple[str, bool]:
        """
        Process a user spoken utterance with multi-slot extraction.

        1. The slot corresponding to the *asked* question gets the
           "guaranteed" (fallback-inclusive) extractor.
        2. All *other* unfilled slots get tentative (confidence-gated)
           extraction attempted on the same utterance.
        3. Profile is persisted immediately after extraction.
        4. The next question is dynamically chosen from remaining missing slots.

        Returns:
            (next_question_text, is_conversation_completed)
        """
        if not transcript or not transcript.strip():
            return self.get_current_question(), self.is_complete

        asked_step = self.current_step
        text = transcript.strip()

        # Log turn to history
        self.history.append({
            "step": asked_step,
            "question": self.get_current_question(),
            "transcript": text,
        })

        if self.is_complete:
            return self.get_current_question(), True

        # --- Guaranteed extraction for the asked step ---
        if asked_step == "name" and not self._slot_filled("name"):
            self.slots["name"] = _extract_name(text)
        elif asked_step == "age" and not self._slot_filled("age"):
            self.slots["age"] = _extract_age(text)
        elif asked_step == "work" and not self._slot_filled("work"):
            self.slots["current_livelihood"] = text
            self.slots["previous_work_experience"] = text
        elif asked_step == "skills" and not self._slot_filled("skills"):
            self.slots["skills"] = text
            self.slots["interests"] = text
        elif asked_step == "preference" and not self._slot_filled("preference"):
            self.slots["employment_preference"] = _extract_preference(text)

        # --- Tentative multi-slot extraction for OTHER unfilled slots ---
        # Note: work and skills share vocabulary (wiring, fitting, etc.) so we
        # never tentatively extract one when the asked question was the other,
        # to avoid cross-contamination.
        if not self._slot_filled("name") and asked_step != "name":
            name = _try_extract_name(text)
            if name:
                self.slots["name"] = name

        if not self._slot_filled("age") and asked_step != "age":
            age = _try_extract_age(text)
            if age is not None:
                self.slots["age"] = age

        # Work and skills share vocabulary (wiring, fitting, etc.).
        # When answering work/skills, only tentatively fill the counterpart
        # if the utterance contains keywords unique to that counterpart.
        _SKILL_ONLY = _SKILL_KEYWORDS - _WORK_KEYWORDS  # e.g. seekhna, aati, learn
        _WORK_ONLY = _WORK_KEYWORDS - _SKILL_KEYWORDS   # e.g. kaam, karta, factory

        if not self._slot_filled("work") and asked_step != "work":
            if asked_step == "skills":
                # Only tentatively fill work if work-unique keywords are present
                tokens = set(re.sub(r"[^\w\s]", " ", text.lower(), flags=re.UNICODE).split())
                if tokens & _WORK_ONLY:
                    self.slots["current_livelihood"] = text
                    self.slots["previous_work_experience"] = text
            else:
                work = _try_extract_work(text)
                if work:
                    self.slots["current_livelihood"] = work
                    self.slots["previous_work_experience"] = work

        if not self._slot_filled("skills") and asked_step != "skills":
            if asked_step == "work":
                # Only tentatively fill skills if skill-unique keywords are present
                tokens = set(re.sub(r"[^\w\s]", " ", text.lower(), flags=re.UNICODE).split())
                if tokens & _SKILL_ONLY:
                    self.slots["skills"] = text
                    self.slots["interests"] = text
            else:
                skills = _try_extract_skills(text)
                if skills:
                    self.slots["skills"] = skills
                    self.slots["interests"] = skills

        if not self._slot_filled("preference") and asked_step != "preference":
            pref = _try_extract_preference(text)
            if pref:
                self.slots["employment_preference"] = pref

        # --- Recompute state and persist ---
        self._recompute_state()
        self.save_profile()

        return self.get_current_question(), self.is_complete

    # ------------------------------------------------------------------
    # Progress & checklist
    # ------------------------------------------------------------------

    def get_progress(self) -> float:
        """Returns progress ratio between 0.0 and 1.0 based on filled slots."""
        return min(1.0, self._filled_count() / len(STEPS))

    def get_checklist(self) -> List[Tuple[str, bool, str]]:
        """
        Returns checklist of collected slots with label, completion bool, and current value.
        """
        checklist = []
        for step_key in STEPS:
            label = STEP_LABELS.get(step_key, step_key)
            filled = self._slot_filled(step_key)
            val = ""
            if step_key == "name":
                val = self.slots.get("name", "")
            elif step_key == "age":
                val = str(self.slots.get("age", "")) if filled else ""
            elif step_key == "work":
                val = (self.slots.get("current_livelihood", "") or "")[:35]
            elif step_key == "skills":
                val = (self.slots.get("skills", "") or "")[:35]
            elif step_key == "preference":
                ep = self.slots.get("employment_preference", "")
                val = ("Self-Emp" if "Self" in ep else "Wage-Emp") if filled else ""
            checklist.append((label, filled, val))
        return checklist

    def save_profile(self) -> Dict[str, Any]:
        """Persist collected slots directly to profile_store.py."""
        return update_profile_slots(self.beneficiary_id, self.slots)

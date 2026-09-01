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


def _extract_name(transcript: str) -> str:
    """Extract name entity from spoken transcript."""
    text = transcript.strip()
    # Remove common conversational prefixes
    patterns = [
        r"^mera naam (.*?) hai$",
        r"^mera naam (.*?)$",
        r"^naam (.*?) hai$",
        r"^majhe naav (.*?) aahe$",
        r"^majhe naav (.*?)$",
        r"^my name is (.*?)$",
        r"^i am (.*?)$",
        r"^main (.*?) hoon$",
        r"^naa peru (.*?)$",
        r"^en peyar (.*?)$",
        r"^aamar naam (.*?)$",
        r"^maru naam (.*?)$",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m and m.group(1).strip():
            candidate = m.group(1).strip()
            # Clean punctuation
            candidate = re.sub(r"[^\w\s]", "", candidate, flags=re.UNICODE).strip()
            if candidate:
                return candidate.title()

    # If no prefix matched, use the cleaned transcript as the name (up to 3 words)
    clean = re.sub(r"[^\w\s]", "", text, flags=re.UNICODE).strip()
    words = clean.split()
    if words:
        return " ".join(words[:3]).title()
    return "Beneficiary"


def _extract_age(transcript: str) -> int:
    """Extract age integer from spoken transcript."""
    text = transcript.lower()
    # Check for direct digits
    digits = re.findall(r"\b\d{1,2}\b", text)
    if digits:
        val = int(digits[0])
        if 14 <= val <= 85:
            return val

    # Check for word numbers
    for word, val in AGE_WORDS.items():
        if word in text:
            return val

    return 25  # Sensible default


def _extract_preference(transcript: str) -> str:
    """Extract wage vs self-employment preference from spoken transcript."""
    text = transcript.lower()
    self_keywords = [
        "apna", "khud", "dukan", "dukaan", "business", "vyavsay", "dhandha",
        "self", "entrepreneur", "boutique", "parlour", "shop", "own", "svatah"
    ]
    for kw in self_keywords:
        if kw in text:
            return "Self Employment (Entrepreneurship / Micro-enterprise)"

    return "Wage Employment (Job)"


class ConversationSession:
    """
    State machine session tracking the progressive voice onboarding conversation.
    """

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
                "age": saved.get("age", 25),
                "current_livelihood": saved.get("current_livelihood", ""),
                "previous_work_experience": saved.get("previous_work_experience", ""),
                "skills": saved.get("skills", ""),
                "interests": saved.get("interests", ""),
                "employment_preference": saved.get("employment_preference", "Wage Employment (Job)"),
                "education_level": saved.get("education_level", "10th Pass"),
                "mobility_constraints": saved.get("mobility_constraints", "Local only (within district)"),
            }
            self.language = self.slots["language"] if self.slots["language"] in QUESTIONS else "Hindi"
            self.district = self.slots["district"]

            # If all key onboarding slots are filled, mark complete
            has_name = bool(self.slots.get("name"))
            has_work = bool(self.slots.get("current_livelihood") or self.slots.get("previous_work_experience"))
            has_skills = bool(self.slots.get("skills") or self.slots.get("interests"))

            if has_name and has_work and has_skills:
                self.current_step_idx = len(STEPS)
                self.is_complete = True
            elif not has_name:
                self.current_step_idx = 0
                self.is_complete = False
            elif not has_work:
                self.current_step_idx = 2
                self.is_complete = False
            elif not has_skills:
                self.current_step_idx = 3
                self.is_complete = False
            else:
                self.current_step_idx = 4
                self.is_complete = False
        else:
            self.current_step_idx = 0
            self.slots = {
                "beneficiary_id": self.beneficiary_id,
                "language": self.language,
                "district": self.district,
                "name": "",
                "age": 25,
                "current_livelihood": "",
                "previous_work_experience": "",
                "skills": "",
                "interests": "",
                "employment_preference": "Wage Employment (Job)",
                "education_level": "10th Pass",
                "mobility_constraints": "Local only (within district)",
            }
            self.is_complete = False

    @property
    def current_step(self) -> str:
        if self.current_step_idx < len(STEPS):
            return STEPS[self.current_step_idx]
        return "complete"

    def get_current_question(self) -> str:
        """Get the localized question text for the current step."""
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

    def process_turn(self, transcript: str) -> Tuple[str, bool]:
        """
        Process a user spoken utterance for the current step, update slots,
        and advance the state machine.

        Returns:
            (next_question_text, is_conversation_completed)
        """
        if not transcript or not transcript.strip():
            return self.get_current_question(), self.is_complete

        step = self.current_step
        text = transcript.strip()

        # Log turn to history
        self.history.append({
            "step": step,
            "question": self.get_current_question(),
            "transcript": text,
        })

        if step == "name":
            extracted_name = _extract_name(text)
            self.slots["name"] = extracted_name
            self.current_step_idx += 1

        elif step == "age":
            extracted_age = _extract_age(text)
            self.slots["age"] = extracted_age
            self.current_step_idx += 1

        elif step == "work":
            self.slots["current_livelihood"] = text
            self.slots["previous_work_experience"] = text
            self.current_step_idx += 1

        elif step == "skills":
            self.slots["skills"] = text
            self.slots["interests"] = text
            self.current_step_idx += 1

        elif step == "preference":
            extracted_pref = _extract_preference(text)
            self.slots["employment_preference"] = extracted_pref
            self.current_step_idx += 1

        # Check completion
        if self.current_step_idx >= len(STEPS):
            self.is_complete = True
            # Persist to profile store
            self.save_profile()

        return self.get_current_question(), self.is_complete

    def get_progress(self) -> float:
        """Returns progress ratio between 0.0 and 1.0."""
        return min(1.0, self.current_step_idx / len(STEPS))

    def get_checklist(self) -> List[Tuple[str, bool, str]]:
        """
        Returns checklist of collected slots with label, completion bool, and current value.
        """
        checklist = []
        for i, step_key in enumerate(STEPS):
            label = STEP_LABELS.get(step_key, step_key)
            is_filled = i < self.current_step_idx
            val = ""
            if step_key == "name":
                val = self.slots.get("name", "")
            elif step_key == "age":
                val = str(self.slots.get("age", "")) if is_filled else ""
            elif step_key == "work":
                val = self.slots.get("current_livelihood", "")[:35]
            elif step_key == "skills":
                val = self.slots.get("skills", "")[:35]
            elif step_key == "preference":
                val = "Self-Emp" if "Self" in self.slots.get("employment_preference", "") else "Wage-Emp" if is_filled else ""

            checklist.append((label, is_filled, val))
        return checklist

    def save_profile(self) -> Dict[str, Any]:
        """Persist collected slots directly to profile_store.py."""
        return update_profile_slots(self.beneficiary_id, self.slots)

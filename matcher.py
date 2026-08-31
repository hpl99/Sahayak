"""
Lightweight trade matcher.

Matches the user's ASR transcript against trade keywords and local
demand scores. Also builds a spoken recommendation in the selected
Indian language.
"""

import re
import pandas as pd


def load_trades(csv_path: str = "data/nsqf_trades.csv") -> pd.DataFrame:
    return pd.read_csv(csv_path)


def _tokenize(text: str) -> set:
    """Lowercase and tokenize Latin/Indic text."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return set(t for t in text.split() if t)


def match_trades(
    transcript: str,
    district: str,
    trades_df: pd.DataFrame,
    top_n: int = 3,
) -> list[dict]:
    """
    Rank trades using keyword overlap + local demand.

    Score = keyword overlap * 2 + local demand score.
    """

    transcript_tokens = _tokenize(transcript)

    demand_col = f"demand_{district.lower().strip()}"

    if demand_col not in trades_df.columns:
        demand_col = "demand_default"

    results = []

    for _, row in trades_df.iterrows():

        trade_keywords = _tokenize(
            str(row["keywords"]).replace("|", " ")
        )

        overlap = transcript_tokens & trade_keywords

        demand_score = float(row[demand_col])

        total_score = len(overlap) * 2 + demand_score

        results.append(
            {
                "trade_name": row["trade_name"],
                "nsqf_level": int(row["nsqf_level"]),
                "sector": row["sector"],
                "matched_keywords": sorted(overlap),
                "demand_score": demand_score,
                "avg_monthly_wage_inr": int(
                    row["avg_monthly_wage_inr"]
                ),
                "score": total_score,
            }
        )

    results.sort(
        key=lambda r: r["score"],
        reverse=True,
    )

    return results[:top_n]


def match_profile(
    profile: dict,
    trades_df: pd.DataFrame,
    district: str = None,
    top_n: int = 3,
) -> list[dict]:
    """
    Rank trades based on a complete Beneficiary Profile.

    Uses:
    - Skills (high weight)
    - Interests (medium weight)
    - Current livelihood (transition weight)
    - Employment preference (self-employment vs wage employment alignment)
    - Mobility constraints (local demand alignment)
    - Education level vs NSQF level compatibility
    - District demand score

    Returns transparent reasons / explanations for each recommendation.
    """
    if not district:
        district = profile.get("district", "nagpur")
    
    district_clean = str(district).lower().strip()
    demand_col = f"demand_{district_clean}"
    if demand_col not in trades_df.columns:
        demand_col = "demand_default"

    skills_text = str(profile.get("skills", "") or "")
    interests_text = str(profile.get("interests", "") or "")
    livelihood_text = str(profile.get("current_livelihood", "") or "")
    emp_pref = str(profile.get("employment_preference", "") or "")
    mobility = str(profile.get("mobility_constraints", "") or "")
    education = str(profile.get("education_level", "") or "")

    skill_tokens = _tokenize(skills_text)
    interest_tokens = _tokenize(interests_text)
    livelihood_tokens = _tokenize(livelihood_text)

    # Specific trade profiles for employment preference weighting
    self_employment_trades = {
        "tailoring & fashion design",
        "mobile repair technician",
        "beautician & wellness",
        "handicrafts & weaving",
        "electrician (domestic)",
        "food processing technician",
        "plumber",
    }
    wage_employment_trades = {
        "retail sales associate",
        "driving cum logistics assistant",
        "welder (fabrication)",
        "solar panel installer",
        "domestic data entry operator",
        "electrician (domestic)",
        "food processing technician",
    }

    results = []

    for _, row in trades_df.iterrows():
        trade_name = str(row["trade_name"])
        trade_lower = trade_name.lower()
        sector = str(row["sector"])
        nsqf_level = int(row["nsqf_level"])
        demand_score = float(row[demand_col])
        wage = int(row["avg_monthly_wage_inr"])

        trade_keywords = _tokenize(str(row["keywords"]).replace("|", " "))
        sector_tokens = _tokenize(sector)

        # 1. Skill overlap (weight = 3)
        skill_overlap = skill_tokens & trade_keywords
        skill_score = len(skill_overlap) * 3.0

        # 2. Interest overlap (weight = 2)
        interest_overlap = interest_tokens & (trade_keywords | sector_tokens | _tokenize(trade_name))
        interest_score = len(interest_overlap) * 2.0

        # 3. Livelihood overlap (weight = 1.5)
        livelihood_overlap = livelihood_tokens & trade_keywords
        livelihood_score = len(livelihood_overlap) * 1.5

        # 4. Employment preference bonus
        emp_bonus = 0.0
        emp_reason = None
        if "self" in emp_pref.lower():
            if trade_lower in self_employment_trades:
                emp_bonus = 2.5
                emp_reason = "✓ Matches self-employment / micro-enterprise preference"
        elif "wage" in emp_pref.lower() or "job" in emp_pref.lower():
            if trade_lower in wage_employment_trades:
                emp_bonus = 2.5
                emp_reason = "✓ Matches wage-employment preference with structured hiring"

        # 5. Demand score
        total_score = skill_score + interest_score + livelihood_score + emp_bonus + demand_score

        # 6. Build transparent explanations
        explanations = []
        if skill_overlap:
            explanations.append(f"✓ Stated skill matches: {', '.join(sorted(skill_overlap))}")
        elif interest_overlap:
            explanations.append(f"✓ Stated interest aligns with {sector} sector ({', '.join(sorted(interest_overlap))})")

        if demand_score >= 7.0:
            dist_display = district.capitalize() if district != "default" else "local market"
            explanations.append(f"✓ High local demand in {dist_display} ({demand_score:.0f}/10)")
        elif demand_score >= 5.0:
            explanations.append(f"✓ Moderate local demand score ({demand_score:.0f}/10)")

        if emp_reason:
            explanations.append(emp_reason)

        if education and education != "No formal education":
            explanations.append(f"✓ Education background ({education}) fits NSQF Level {nsqf_level}")

        if not explanations:
            explanations.append(f"✓ Foundation NSQF Level {nsqf_level} pathway with ₹{wage:,}/mo avg wage")

        all_matched_keywords = sorted(skill_overlap | interest_overlap | livelihood_overlap)

        results.append(
            {
                "trade_name": trade_name,
                "nsqf_level": nsqf_level,
                "sector": sector,
                "demand_score": demand_score,
                "avg_monthly_wage_inr": wage,
                "matched_keywords": all_matched_keywords,
                "score": total_score,
                "explanations": explanations,
                "explanation_text": "\n".join(explanations),
            }
        )

    results.sort(
        key=lambda r: r["score"],
        reverse=True,
    )

    return results[:top_n]



# ---------------------------------------------------------------------------
# MULTILINGUAL SPOKEN RECOMMENDATION
# ---------------------------------------------------------------------------

def build_recommendation_text(
    matches: list[dict],
    language_label: str = "Hindi",
) -> str:
    """
    Build a recommendation in the language selected by the user.

    The trade names and sector names come from the CSV and therefore
    remain unchanged. The surrounding recommendation is localized.
    """

    translations = {

        "Hindi": {
            "no_match": (
                "हमें आपके लिए कोई मजबूत विकल्प नहीं मिला। "
                "कृपया अपनी रुचियों और अनुभव के बारे में थोड़ा और बताएं।"
            ),

            "best": (
                "आपने जो जानकारी साझा की है, उसके आधार पर आपके लिए "
                "सबसे अच्छा विकल्प {trade} है। यह {sector} क्षेत्र में "
                "एनएसक्यूएफ स्तर {level} का कोर्स है। इस क्षेत्र में "
                "स्थानीय मांग अच्छी है और औसत मासिक वेतन लगभग "
                "{wage} रुपये है।"
            ),

            "other": (
                "आपके लिए अन्य अच्छे विकल्प {options} हैं।"
            ),
        },

        "Marathi": {
            "no_match": (
                "तुमच्यासाठी योग्य पर्याय सापडला नाही. "
                "कृपया तुमच्या आवडी आणि अनुभवाबद्दल आणखी सांगा."
            ),

            "best": (
                "तुम्ही दिलेल्या माहितीनुसार तुमच्यासाठी सर्वोत्तम "
                "पर्याय {trade} आहे. हा {sector} क्षेत्रातील "
                "एनएसक्यूएफ स्तर {level} चा अभ्यासक्रम आहे. "
                "या क्षेत्रात स्थानिक मागणी चांगली आहे आणि सरासरी "
                "मासिक वेतन सुमारे {wage} रुपये आहे."
            ),

            "other": (
                "तुमच्यासाठी इतर चांगले पर्याय {options} आहेत."
            ),
        },

        "Telugu": {
            "no_match": (
                "మీకు సరైన ఎంపికను కనుగొనలేకపోయాము. "
                "దయచేసి మీ ఆసక్తులు మరియు అనుభవం గురించి మరింత చెప్పండి."
            ),

            "best": (
                "మీరు అందించిన సమాచారం ఆధారంగా మీకు ఉత్తమమైన ఎంపిక "
                "{trade}. ఇది {sector} రంగంలో ఎన్ఎస్‌క్యూఎఫ్ స్థాయి "
                "{level} కోర్సు. ఈ రంగంలో స్థానిక డిమాండ్ బాగుంది "
                "మరియు సగటు నెలవారీ వేతనం సుమారు {wage} రూపాయలు."
            ),

            "other": (
                "మీకు ఇతర మంచి ఎంపికలు {options}."
            ),
        },

        "Tamil": {
            "no_match": (
                "உங்களுக்கு பொருத்தமான சிறந்த தேர்வை எங்களால் "
                "கண்டுபிடிக்க முடியவில்லை. உங்கள் ஆர்வங்கள் மற்றும் "
                "அனுபவத்தைப் பற்றி மேலும் கூறுங்கள்."
            ),

            "best": (
                "நீங்கள் பகிர்ந்த தகவலின் அடிப்படையில் உங்களுக்கு "
                "சிறந்த தேர்வு {trade}. இது {sector} துறையில் "
                "என்எஸ்க்யூஎஃப் நிலை {level} பயிற்சி. இந்தத் துறையில் "
                "உள்ளூர் தேவை நன்றாக உள்ளது மற்றும் சராசரி மாத சம்பளம் "
                "சுமார் {wage} ரூபாய்."
            ),

            "other": (
                "உங்களுக்கு மற்ற நல்ல தேர்வுகள் {options}."
            ),
        },

        "Bengali": {
            "no_match": (
                "আপনার জন্য উপযুক্ত কোনো শক্তিশালী বিকল্প খুঁজে পাইনি। "
                "আপনার আগ্রহ এবং অভিজ্ঞতা সম্পর্কে আরও বলুন।"
            ),

            "best": (
                "আপনি যে তথ্য দিয়েছেন তার ভিত্তিতে আপনার জন্য "
                "সবচেয়ে ভালো বিকল্প {trade}। এটি {sector} ক্ষেত্রে "
                "এনএসকিউএফ স্তর {level}-এর একটি কোর্স। এই ক্ষেত্রে "
                "স্থানীয় চাহিদা ভালো এবং গড় মাসিক বেতন প্রায় "
                "{wage} টাকা।"
            ),

            "other": (
                "আপনার জন্য অন্যান্য ভালো বিকল্প হলো {options}।"
            ),
        },

        "Gujarati": {
            "no_match": (
                "તમારા માટે યોગ્ય વિકલ્પ મળી શક્યો નથી. "
                "કૃપા કરીને તમારી રુચિઓ અને અનુભવ વિશે વધુ જણાવો."
            ),

            "best": (
                "તમે આપેલી માહિતીના આધારે તમારા માટે શ્રેષ્ઠ વિકલ્પ "
                "{trade} છે. આ {sector} ક્ષેત્રમાં એનએસક્યુએફ સ્તર "
                "{level}નો કોર્સ છે. આ ક્ષેત્રમાં સ્થાનિક માંગ સારી છે "
                "અને સરેરાશ માસિક પગાર આશરે {wage} રૂપિયા છે."
            ),

            "other": (
                "તમારા માટે અન્ય સારા વિકલ્પો {options} છે."
            ),
        },
    }

    # Default to Hindi.
    lang = language_label if language_label in translations else "Hindi"

    t = translations[lang]

    if not matches:
        return t["no_match"]

    top = matches[0]

    result = t["best"].format(
        trade=top["trade_name"],
        sector=top["sector"],
        level=top["nsqf_level"],
        wage=f"{top['avg_monthly_wage_inr']:,}",
    )

    if len(matches) > 1:

        alt_names = ", ".join(
            m["trade_name"]
            for m in matches[1:]
        )

        result += " " + t["other"].format(
            options=alt_names
        )

    return result
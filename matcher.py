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
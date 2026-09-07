"""Lightweight conversation-language and presentation helpers."""

from __future__ import annotations

import re
from typing import Literal


Language = Literal["english", "urdu", "roman_urdu"]

_URDU_SCRIPT_RE = re.compile(r"[\u0600-\u06ff]")
_ROMAN_URDU_WORDS = {
    "asaan",
    "alfaaz",
    "banao",
    "banwana",
    "batao",
    "chahiye",
    "dikhao",
    "hai",
    "hain",
    "karni",
    "karwana",
    "kahan",
    "ke",
    "ki",
    "kitni",
    "kya",
    "mein",
    "mujhe",
    "pehle",
    "samjhao",
    "wala",
    "wale",
}
_ENGLISH_SIGNAL_WORDS = {
    "appointment",
    "appointments",
    "book",
    "documents",
    "explain",
    "fee",
    "find",
    "how",
    "show",
    "what",
    "where",
}

_SIMPLE_PHRASES = (
    "simple language",
    "simple words",
    "easier to understand",
    "easy words",
    "asaan alfaaz",
    "asan alfaaz",
    "samjhao",
    "samjha dein",
    "آسان الفاظ",
    "سمجھائیں",
    "سمجھاؤ",
)


def detect_language(text: str, previous: str | None = None) -> Language:
    """Detect the turn language while retaining it for very short replies."""
    normalized = text.casefold().strip()
    if re.search(r"\b(?:in english|english mein|english me)\b", normalized):
        return "english"
    if re.search(r"\b(?:in urdu|urdu mein|urdu me)\b", normalized):
        return "urdu"
    if "انگریزی" in normalized:
        return "english"
    if "اردو" in normalized:
        return "urdu"
    if _URDU_SCRIPT_RE.search(text):
        return "urdu"

    words = set(re.findall(r"[a-z]+", normalized))
    if words & _ROMAN_URDU_WORDS:
        return "roman_urdu"
    if words & _ENGLISH_SIGNAL_WORDS:
        return "english"
    if previous in {"english", "urdu", "roman_urdu"} and len(words) <= 2:
        return previous
    return "english"


def is_simple_language_request(text: str) -> bool:
    normalized = text.casefold()
    return any(phrase in normalized for phrase in _SIMPLE_PHRASES)


def is_language_override_request(text: str) -> bool:
    normalized = text.casefold()
    return bool(
        re.search(r"\b(?:in english|english mein|english me|in urdu|urdu mein|urdu me)\b", normalized)
        or "انگریزی" in normalized
        or "اردو میں" in normalized
    )


def generation_instruction(language: str, *, simple: bool = False) -> str:
    labels = {
        "english": "English",
        "urdu": "Urdu script",
        "roman_urdu": "natural Roman Urdu",
    }
    instruction = (
        f"Respond in {labels.get(language, 'English')}. Preserve names, numbers, "
        "dates, official terms, and source meaning exactly."
    )
    if simple:
        instruction += (
            " Use short, clear sentences and simple words. Explain what the "
            "information means for the citizen and any supported deadline or next "
            "action. Do not invent an action that is absent from the context."
        )
    return instruction


_MESSAGES = {
    "clarify_service": {
        "english": "Please clarify which government service you need.",
        "roman_urdu": "Meherbani karke batayein ke aap ko kis government service mein madad chahiye.",
        "urdu": "براہِ کرم بتائیں کہ آپ کو کس سرکاری سروس میں مدد چاہیے۔",
    },
    "upload_required": {
        "english": "Please upload or provide the document you want me to inspect.",
        "roman_urdu": "Jis document ko dekhna hai, meherbani karke woh upload karein.",
        "urdu": "جس دستاویز کو دیکھنا ہے، براہِ کرم اسے اپ لوڈ کریں۔",
    },
    "verification_failed": {
        "english": "I couldn't verify this response against the available source, so I won't present it as confirmed information.",
        "roman_urdu": "Main is jawab ko available source se verify nahin kar saka, is liye ise confirmed maloomat ke taur par pesh nahin karunga.",
        "urdu": "میں اس جواب کو دستیاب ماخذ سے تصدیق نہیں کر سکا، اس لیے اسے مصدقہ معلومات کے طور پر پیش نہیں کروں گا۔",
    },
    "no_context": {
        "english": "I couldn't find reliable information for this request in the current knowledge base.",
        "roman_urdu": "Mujhe current knowledge base mein is sawal ke liye bharosemand maloomat nahin mili.",
        "urdu": "مجھے موجودہ معلوماتی ذخیرے میں اس سوال کے لیے قابلِ اعتماد معلومات نہیں ملیں۔",
    },
    "checklist_not_found": {
        "english": "I couldn't find trusted checklist requirements for this service in the current knowledge base.",
        "roman_urdu": "Mujhe current knowledge base mein is service ki bharosemand checklist nahin mili.",
        "urdu": "مجھے موجودہ معلوماتی ذخیرے میں اس سروس کی قابلِ اعتماد چیک لسٹ نہیں ملی۔",
    },
    "fee_not_found": {
        "english": "I couldn't find reliable, verified fee information for this service in the current knowledge base.",
        "roman_urdu": "Mujhe current knowledge base mein is service ki verified fee maloomat nahin mili.",
        "urdu": "مجھے موجودہ معلوماتی ذخیرے میں اس سروس کی تصدیق شدہ فیس کی معلومات نہیں ملیں۔",
    },
    "booking_verification_failed": {
        "english": "I couldn't verify that the demo booking was recorded, so no booking is being confirmed.",
        "roman_urdu": "Demo booking record verify nahin hua, is liye booking confirm nahin ki ja rahi.",
        "urdu": "ڈیمو بکنگ کا ریکارڈ تصدیق نہیں ہو سکا، اس لیے بکنگ کی تصدیق نہیں کی جا رہی۔",
    },
    "presentation_context_required": {
        "english": "Please provide the information or document you want me to explain.",
        "roman_urdu": "Jis maloomat ya document ko samajhna hai, woh provide karein.",
        "urdu": "جس معلومات یا دستاویز کو سمجھنا ہے، براہِ کرم وہ فراہم کریں۔",
    },
    "lookup_missing_location": {
        "english": "Which city or region should I search for a {service} service center in?",
        "roman_urdu": "{service} service center kis shehar ya ilaqe mein dhoondun?",
        "urdu": "{service} سروس سینٹر کس شہر یا علاقے میں تلاش کروں؟",
    },
    "lookup_no_results": {
        "english": "I couldn't find a {service} service center for {location} in the current dataset.",
        "roman_urdu": "Current dataset mein {location} ke liye {service} service center nahin mila.",
        "urdu": "موجودہ ڈیٹا میں {location} کے لیے {service} سروس سینٹر نہیں ملا۔",
    },
    "lookup_unsupported": {
        "english": "Service-center lookup is not available for {service}.",
        "roman_urdu": "{service} ke liye service-center lookup available nahin hai.",
        "urdu": "{service} کے لیے سروس سینٹر تلاش کی سہولت دستیاب نہیں ہے۔",
    },
    "lookup_found": {
        "english": "I found these {service} service centers for {location}:",
        "roman_urdu": "{location} ke liye yeh {service} service centers mile hain:",
        "urdu": "{location} کے لیے یہ {service} سروس سینٹر ملے ہیں:",
    },
    "office_selection": {
        "english": "Several matching offices are available. Which office should I use for the demo appointment? Reply with its name or number:",
        "roman_urdu": "Kai matching offices hain. Demo appointment ke liye kaunsa office use karun? Naam ya number batayein:",
        "urdu": "کئی متعلقہ دفاتر دستیاب ہیں۔ ڈیمو اپائنٹمنٹ کے لیے کون سا دفتر استعمال کروں؟ نام یا نمبر بتائیں:",
    },
    "invalid_office": {
        "english": "There are only {count} matching offices. Please choose an office from 1 to {count}.",
        "roman_urdu": "Sirf {count} matching offices hain. 1 se {count} tak koi office chunein.",
        "urdu": "صرف {count} متعلقہ دفاتر ہیں۔ 1 سے {count} تک کوئی دفتر منتخب کریں۔",
    },
    "availability_not_configured": {
        "english": "No demo appointment schedule is configured for {office}. This does not reflect real government availability.",
        "roman_urdu": "{office} ke liye demo appointment schedule configured nahin hai. Yeh real government availability nahin dikhata.",
        "urdu": "{office} کے لیے ڈیمو اپائنٹمنٹ شیڈول موجود نہیں ہے۔ یہ حقیقی سرکاری دستیابی نہیں دکھاتا۔",
    },
    "availability_empty": {
        "english": "No simulated slots remain for {office} on {date}. Check the official government booking system for real availability.",
        "roman_urdu": "{office} mein {date} ke liye koi simulated slot baqi nahin. Real availability official booking system par check karein.",
        "urdu": "{office} میں {date} کے لیے کوئی نقلی سلاٹ باقی نہیں۔ حقیقی دستیابی سرکاری بکنگ سسٹم پر دیکھیں۔",
    },
    "availability": {
        "english": "Simulated prototype availability — not live government availability.\nOffice: {office}\nDate: {date}\nAvailable demo slots: {slots}\nA real appointment must be checked through the official government system.",
        "roman_urdu": "Simulated prototype availability — yeh live government availability nahin hai.\nOffice: {office}\nDate: {date}\nAvailable demo slots: {slots}\nReal appointment official government system par check karein.",
        "urdu": "نقلی پروٹوٹائپ دستیابی — یہ براہِ راست سرکاری دستیابی نہیں ہے۔\nدفتر: {office}\nتاریخ: {date}\nدستیاب ڈیمو سلاٹس: {slots}\nحقیقی اپائنٹمنٹ سرکاری نظام پر چیک کریں۔",
    },
    "booking_confirmed": {
        "english": "Simulated booking confirmed (demo only).\nOffice: {office}\nDate: {date}\nTime: {time}\nDemo reference: {reference}\nNo real government appointment was created; use the official booking system for an actual appointment.",
        "roman_urdu": "Simulated booking confirm ho gayi (sirf demo).\nOffice: {office}\nDate: {date}\nTime: {time}\nDemo reference: {reference}\nKoi real government appointment nahin bani; asal appointment ke liye official booking system use karein.",
        "urdu": "نقلی بکنگ کی تصدیق ہو گئی (صرف ڈیمو)۔\nدفتر: {office}\nتاریخ: {date}\nوقت: {time}\nڈیمو حوالہ: {reference}\nکوئی حقیقی سرکاری اپائنٹمنٹ نہیں بنی؛ اصل اپائنٹمنٹ کے لیے سرکاری بکنگ سسٹم استعمال کریں۔",
    },
    "booking_missing_time": {
        "english": "Which demo appointment time would you like to book?",
        "roman_urdu": "Aap kaunsa demo appointment time book karna chahte hain?",
        "urdu": "آپ ڈیمو اپائنٹمنٹ کے لیے کون سا وقت بک کرنا چاہتے ہیں؟",
    },
    "booking_slot_not_found": {
        "english": "The {time} demo slot does not exist for {office} on {date}.",
        "roman_urdu": "{office} mein {date} ko {time} ka demo slot maujood nahin hai.",
        "urdu": "{office} میں {date} کو {time} کا ڈیمو سلاٹ موجود نہیں ہے۔",
    },
    "booking_unavailable": {
        "english": "The {time} demo slot for {office} is already unavailable or booked in this simulation.",
        "roman_urdu": "{office} ka {time} demo slot is simulation mein available nahin ya pehle book ho chuka hai.",
        "urdu": "{office} کا {time} ڈیمو سلاٹ اس نقلی نظام میں دستیاب نہیں یا پہلے بک ہو چکا ہے۔",
    },
    "unsupported_action": {
        "english": "This action is not supported yet. I can look up service centers and simulate appointment slots.",
        "roman_urdu": "Yeh action abhi supported nahin hai. Main service centers dhoond sakta hoon aur appointment slots simulate kar sakta hoon.",
        "urdu": "یہ کارروائی ابھی دستیاب نہیں ہے۔ میں سروس سینٹر تلاش اور اپائنٹمنٹ سلاٹس کی نقل کر سکتا ہوں۔",
    },
    "journey_orientation": {
        "english": "I can guide you through the {service} process, including required documents, trusted fee information, service centers, and demo appointment booking. A good place to start is the required documents. Would you like to see them?",
        "roman_urdu": "Main {service} process mein required documents, bharosemand fee maloomat, service centers aur demo appointment booking ke bare mein guide kar sakta hoon. Behtar hai required documents se shuru karein. Kya aap woh dekhna chahenge?",
        "urdu": "میں {service} کے عمل میں مطلوبہ کاغذات، قابلِ اعتماد فیس کی معلومات، سروس سینٹرز اور ڈیمو اپائنٹمنٹ بکنگ کے بارے میں رہنمائی کر سکتا ہوں۔ بہتر ہے مطلوبہ کاغذات سے شروع کریں۔ کیا آپ وہ دیکھنا چاہیں گے؟",
    },
    "journey_service_needed": {
        "english": "Which government service should I show progress for?",
        "roman_urdu": "Kis government service ki progress dikhaun?",
        "urdu": "کس سرکاری سروس کی پیش رفت دکھاؤں؟",
    },
    "journey_title": {
        "english": "{service} assistance journey",
        "roman_urdu": "{service} madad ka safar",
        "urdu": "{service} معاونتی سفر",
    },
    "journey_requirements_done": {"english": "✓ Requirements reviewed", "roman_urdu": "✓ Requirements dekh liye gaye", "urdu": "✓ مطلوبہ کاغذات دیکھ لیے گئے"},
    "journey_requirements_pending": {"english": "○ Requirements not reviewed yet", "roman_urdu": "○ Requirements abhi nahin dekhe", "urdu": "○ مطلوبہ کاغذات ابھی نہیں دیکھے گئے"},
    "journey_fees_done": {"english": "✓ Fee information reviewed", "roman_urdu": "✓ Fee maloomat dekh li gayi", "urdu": "✓ فیس کی معلومات دیکھ لی گئیں"},
    "journey_fees_pending": {"english": "○ Fee information not reviewed yet", "roman_urdu": "○ Fee maloomat abhi nahin dekhi", "urdu": "○ فیس کی معلومات ابھی نہیں دیکھی گئیں"},
    "journey_center_located": {"english": "✓ Service centers located", "roman_urdu": "✓ Service centers mil gaye", "urdu": "✓ سروس سینٹرز تلاش ہو گئے"},
    "journey_center_selected": {"english": "✓ Service center selected", "roman_urdu": "✓ Service center select ho gaya", "urdu": "✓ سروس سینٹر منتخب ہو گیا"},
    "journey_center_pending": {"english": "○ Service center not located yet", "roman_urdu": "○ Service center abhi nahin mila", "urdu": "○ سروس سینٹر ابھی تلاش نہیں ہوا"},
    "journey_slots_checked": {"english": "◐ Demo appointment availability checked; not booked", "roman_urdu": "◐ Demo appointment availability check hui; booking nahin hui", "urdu": "◐ ڈیمو اپائنٹمنٹ کی دستیابی دیکھی گئی؛ بکنگ نہیں ہوئی"},
    "journey_booking_done": {"english": "✓ Demo appointment booked", "roman_urdu": "✓ Demo appointment book ho gayi", "urdu": "✓ ڈیمو اپائنٹمنٹ بک ہو گئی"},
    "journey_booking_pending": {"english": "○ Demo appointment not booked yet", "roman_urdu": "○ Demo appointment abhi book nahin hui", "urdu": "○ ڈیمو اپائنٹمنٹ ابھی بک نہیں ہوئی"},
    "journey_disclaimer": {
        "english": "This tracks assistance provided by PakAssist, not verified government completion.",
        "roman_urdu": "Yeh PakAssist ki di hui madad track karta hai, verified government completion nahin.",
        "urdu": "یہ پاک اسسٹ کی فراہم کردہ مدد کو ٹریک کرتا ہے، تصدیق شدہ سرکاری تکمیل کو نہیں۔",
    },
}


def message(key: str, language: str, **values: object) -> str:
    choices = _MESSAGES[key]
    return choices.get(language, choices["english"]).format(**values)

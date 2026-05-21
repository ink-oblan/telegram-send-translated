from __future__ import annotations

import difflib
import re

# ISO 639-1 code -> canonical English name. Comprehensive enough to cover
# essentially every language a user would request. The codes double as BCP-47
# language codes for providers that need them (e.g. Google Translation LLM).
LANGUAGE_NAMES: dict[str, str] = {
    "aa": "Afar",
    "ab": "Abkhazian",
    "af": "Afrikaans",
    "ak": "Akan",
    "am": "Amharic",
    "an": "Aragonese",
    "ar": "Arabic",
    "as": "Assamese",
    "az": "Azerbaijani",
    "be": "Belarusian",
    "bg": "Bulgarian",
    "bm": "Bambara",
    "bn": "Bengali",
    "bo": "Tibetan",
    "br": "Breton",
    "bs": "Bosnian",
    "ca": "Catalan",
    "ce": "Chechen",
    "co": "Corsican",
    "cs": "Czech",
    "cy": "Welsh",
    "da": "Danish",
    "de": "German",
    "dv": "Divehi",
    "dz": "Dzongkha",
    "ee": "Ewe",
    "el": "Greek",
    "en": "English",
    "eo": "Esperanto",
    "es": "Spanish",
    "et": "Estonian",
    "eu": "Basque",
    "fa": "Persian",
    "ff": "Fula",
    "fi": "Finnish",
    "fo": "Faroese",
    "fr": "French",
    "fy": "Western Frisian",
    "ga": "Irish",
    "gd": "Scottish Gaelic",
    "gl": "Galician",
    "gn": "Guarani",
    "gu": "Gujarati",
    "ha": "Hausa",
    "he": "Hebrew",
    "hi": "Hindi",
    "hr": "Croatian",
    "ht": "Haitian Creole",
    "hu": "Hungarian",
    "hy": "Armenian",
    "id": "Indonesian",
    "ig": "Igbo",
    "is": "Icelandic",
    "it": "Italian",
    "iu": "Inuktitut",
    "ja": "Japanese",
    "jv": "Javanese",
    "ka": "Georgian",
    "kk": "Kazakh",
    "km": "Khmer",
    "kn": "Kannada",
    "ko": "Korean",
    "ku": "Kurdish",
    "ky": "Kyrgyz",
    "la": "Latin",
    "lb": "Luxembourgish",
    "lo": "Lao",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "mg": "Malagasy",
    "mi": "Maori",
    "mk": "Macedonian",
    "ml": "Malayalam",
    "mn": "Mongolian",
    "mr": "Marathi",
    "ms": "Malay",
    "mt": "Maltese",
    "my": "Burmese",
    "ne": "Nepali",
    "nl": "Dutch",
    "no": "Norwegian",
    "ny": "Nyanja",
    "oc": "Occitan",
    "om": "Oromo",
    "or": "Odia",
    "pa": "Punjabi",
    "pl": "Polish",
    "ps": "Pashto",
    "pt": "Portuguese",
    "qu": "Quechua",
    "rm": "Romansh",
    "rn": "Rundi",
    "ro": "Romanian",
    "ru": "Russian",
    "rw": "Kinyarwanda",
    "sa": "Sanskrit",
    "sd": "Sindhi",
    "se": "Northern Sami",
    "sg": "Sango",
    "si": "Sinhala",
    "sk": "Slovak",
    "sl": "Slovenian",
    "sm": "Samoan",
    "sn": "Shona",
    "so": "Somali",
    "sq": "Albanian",
    "sr": "Serbian",
    "ss": "Swati",
    "st": "Southern Sotho",
    "su": "Sundanese",
    "sv": "Swedish",
    "sw": "Swahili",
    "ta": "Tamil",
    "te": "Telugu",
    "tg": "Tajik",
    "th": "Thai",
    "ti": "Tigrinya",
    "tk": "Turkmen",
    "tl": "Filipino",
    "tn": "Tswana",
    "to": "Tongan",
    "tr": "Turkish",
    "ts": "Tsonga",
    "tt": "Tatar",
    "ug": "Uyghur",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "uz": "Uzbek",
    "ve": "Venda",
    "vi": "Vietnamese",
    "wo": "Wolof",
    "xh": "Xhosa",
    "yi": "Yiddish",
    "yo": "Yoruba",
    "za": "Zhuang",
    "zh": "Chinese",
    "zu": "Zulu",
}

# Common alternate spellings users may type for a language above.
_ALIASES: dict[str, str] = {
    "farsi": "fa",
    "mandarin": "zh",
    "castilian": "es",
    "tagalog": "tl",
    "oriya": "or",
    "myanmar": "my",
    "bangla": "bn",
    "moldovan": "ro",
    "flemish": "nl",
}

_NAME_TO_CODE: dict[str, str] = {
    name.lower(): code for code, name in LANGUAGE_NAMES.items()
}

# Every recognized language name, sorted — the pool for typo suggestions.
LANGUAGE_LIST: tuple[str, ...] = tuple(sorted(LANGUAGE_NAMES.values()))

# A prefix is an alphabetic token (plus spaces/hyphens) up to 20 chars,
# followed by a colon. The body (DOTALL) keeps any further colons intact.
_PREFIX_RE = re.compile(r"^\s*([A-Za-z][A-Za-z \-]{0,19})\s*:\s*(.+)$", re.DOTALL)


def _to_code(value: str) -> str | None:
    """Resolve an ISO 639-1 code, language name, or known alias to a code."""
    key = value.strip().lower()
    if key in LANGUAGE_NAMES:
        return key
    if key in _NAME_TO_CODE:
        return _NAME_TO_CODE[key]
    return _ALIASES.get(key)


def normalize_language(value: str) -> str | None:
    """Map a code, name, or alias to the canonical English language name.

    Returns None when the value is not an exact match for a known language;
    near-misses are left for suggest_language() to handle.
    """
    code = _to_code(value)
    return LANGUAGE_NAMES[code] if code is not None else None


def to_language_code(value: str) -> str | None:
    """Map a code, name, or alias to a BCP-47 language code, or None."""
    return _to_code(value)


def resolve_target(value: str) -> str | None:
    """Resolve a /setlang argument to a canonical language name, or None."""
    return normalize_language(value)


def suggest_language(value: str) -> list[str]:
    """Up to 3 likely languages for a near-miss.

    Prefix matches come first (so a truncated word like ``Ukraini`` or ``Chi``
    resolves to ``Ukrainian`` / ``Chinese``), then fuzzy matches catch typos
    such as ``Ukrannian``.
    """
    key = value.strip().lower()
    if len(key) < 2:
        return []
    out: list[str] = []
    for name in LANGUAGE_LIST:
        if name.lower().startswith(key):
            out.append(name)
    by_lower = {name.lower(): name for name in LANGUAGE_LIST}
    for match in difflib.get_close_matches(key, by_lower, n=5, cutoff=0.6):
        name = by_lower[match]
        if name not in out:
            out.append(name)
    return out[:3]


def parse_query(text: str) -> tuple[str | None, str]:
    """Split an optional ``lang: body`` override prefix off an inline query.

    Returns ``(target_language, body)``. ``target_language`` is None when no
    *recognized* language prefix is present; an ordinary colon in the text
    (e.g. ``Note: buy milk``) is left untouched as part of the body.
    """
    match = _PREFIX_RE.match(text)
    if match:
        candidate, body = match.group(1).strip(), match.group(2).strip()
        target = normalize_language(candidate)
        if target is not None and body:
            return target, body
    return None, text.strip()

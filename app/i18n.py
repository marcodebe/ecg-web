from typing import Optional

MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "auth_error": "Missing or invalid API key.",
        "invalid_layout": "Invalid layout. Accepted values: {values}",
        "invalid_paper": "Invalid paper format. Accepted values: {values}",
        "invalid_format": "Invalid output format. Accepted values: {values}",
        "conversion_error": "Error converting DICOM file: {error}",
    },
    "it": {
        "auth_error": "API key mancante o non valida.",
        "invalid_layout": "Layout non valido. Valori accettati: {values}",
        "invalid_paper": "Formato carta non valido. Valori accettati: {values}",
        "invalid_format": "Formato output non valido. Valori accettati: {values}",
        "conversion_error": "Errore nella conversione del file DICOM: {error}",
    },
}

FALLBACK = "en"


def detect_language(accept_language: Optional[str]) -> str:
    """Restituisce il codice lingua da usare in base all'header Accept-Language."""
    if not accept_language:
        return FALLBACK

    available = set(MESSAGES.keys())
    candidates: list[tuple[str, float]] = []

    for token in accept_language.split(","):
        token = token.strip()
        if ";q=" in token:
            tag, q_str = token.split(";q=", 1)
            try:
                quality = float(q_str)
            except ValueError:
                quality = 0.0
        else:
            tag = token
            quality = 1.0
        candidates.append((tag.strip().lower(), quality))

    candidates.sort(key=lambda x: x[1], reverse=True)

    for tag, _ in candidates:
        if tag in available:
            return tag
        base = tag.split("-")[0]
        if base in available:
            return base

    return FALLBACK


def t(key: str, lang: str, **kwargs: object) -> str:
    """Traduce una chiave nella lingua richiesta, con fallback all'inglese."""
    messages = MESSAGES.get(lang, MESSAGES[FALLBACK])
    template = messages.get(key, MESSAGES[FALLBACK].get(key, key))
    return template.format(**kwargs) if kwargs else template

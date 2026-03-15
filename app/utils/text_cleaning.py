from __future__ import annotations

import re


DIRECT_TEXT_REPAIRS = {
    '\u2022': '; ',
    '\u00b7': '; ',
    '\u2026': '...',
}

URL_PATTERN = re.compile(r'https?://\S+|www\.\S+|mailto:\S+', re.IGNORECASE)
EMAIL_PATTERN = re.compile(r'\b[\w.+-]+@[\w.-]+\.\w+\b', re.IGNORECASE)
NON_WORD_SEPARATOR_PATTERN = re.compile(r'[\u2012-\u2015\u2212]')
REPEATED_CONJUNCTION_PATTERN = re.compile(r'\b(and|or)\s+\1\b', re.IGNORECASE)


def repair_text_artifacts(text: str) -> str:
    repaired = text

    if any(marker in text for marker in ('â', 'Â')):
        try:
            repaired = text.encode('latin-1').decode('utf-8')
        except UnicodeError:
            repaired = text

    for broken, fixed in DIRECT_TEXT_REPAIRS.items():
        repaired = repaired.replace(broken, fixed)

    repaired = repaired.replace('\xa0', ' ')
    repaired = NON_WORD_SEPARATOR_PATTERN.sub('-', repaired)
    repaired = repaired.replace('&shift', '& shift')
    repaired = repaired.replace('Mc and Cain', 'McCain')
    return repaired


def normalize_whitespace(text: str | None) -> str | None:
    if text is None:
        return None

    cleaned = repair_text_artifacts(str(text)).replace('\r\n', '\n').replace('\r', '\n')
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    cleaned = re.sub(r' ?\n ?', '\n', cleaned)
    cleaned = cleaned.strip()
    return cleaned or None


def flatten_text(text: str | None) -> str | None:
    cleaned = normalize_whitespace(text)
    if not cleaned:
        return None
    cleaned = cleaned.replace('\n', ' ')
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned or None


def strip_urls_and_emails(text: str) -> str:
    cleaned = URL_PATTERN.sub(' ', text)
    cleaned = EMAIL_PATTERN.sub(' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def alpha_word_count(text: str) -> int:
    return len(re.findall(r'\b[a-zA-Z]{2,}\b', text))


def link_like_token_ratio(text: str) -> float:
    tokens = re.findall(r'\S+', text)
    if not tokens:
        return 0.0

    link_like = 0
    for token in tokens:
        if URL_PATTERN.search(token) or EMAIL_PATTERN.search(token):
            link_like += 1
    return link_like / len(tokens)


def normalize_punctuation(text: str) -> str:
    cleaned = repair_text_artifacts(text)
    cleaned = cleaned.replace('\u201c', '"').replace('\u201d', '"').replace('\u2019', "'").replace('\u2018', "'")
    cleaned = re.sub(r'\s+([,.;:!?])', r'\1', cleaned)
    cleaned = re.sub(r'([,.;:!?])(?!\s|$)', r'\1 ', cleaned)
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)
    cleaned = REPEATED_CONJUNCTION_PATTERN.sub(r'\1', cleaned)
    return cleaned.strip()


def contains_meaningful_publication_text(text: str) -> bool:
    stripped = strip_urls_and_emails(text)
    non_whitespace_length = len(re.sub(r'\s+', '', stripped))
    if non_whitespace_length < 30:
        return False
    if link_like_token_ratio(text) > 0.40:
        return False
    if alpha_word_count(stripped) < 8:
        return False
    return True

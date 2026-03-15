from __future__ import annotations

from dataclasses import dataclass
import re

from app.utils.text_cleaning import normalize_punctuation, normalize_whitespace


LEAD_IN_PATTERNS = [
    re.compile(
        r'^(?:need an expert on|looking for academic comment on|looking for comment on|looking for an expert on|seeking academic comment on|seeking expert comment on|academic expert on|academic comment on|need academic comment on|need comment on|expert on|comment on)\s*[:,-]?\s*',
        re.IGNORECASE,
    ),
]
GENERIC_TAIL_PATTERNS = [
    re.compile(
        r'\binterested in policy implications, regional context, and current developments\.?$',
        re.IGNORECASE,
    ),
    re.compile(
        r'\bpolicy implications, regional context, and current developments\.?$',
        re.IGNORECASE,
    ),
]
ABBREVIATION_PATTERNS = [
    (re.compile(r'\bM\.?\s*E\.?\b', re.IGNORECASE), 'Middle East'),
    (re.compile(r'\bI\.?\s*H\.?\s*L\.?\b', re.IGNORECASE), 'international humanitarian law'),
]
CANONICAL_PHRASES = [
    ('Middle East', re.compile(r'\bmiddle east\b', re.IGNORECASE)),
    ('international humanitarian law', re.compile(r'\binternational humanitarian law\b', re.IGNORECASE)),
    ('international law', re.compile(r'\binternational law\b|\bhumanitarian law\b', re.IGNORECASE)),
    ('humanitarian access', re.compile(r'\bhumanitarian access\b', re.IGNORECASE)),
    ('civilian harm', re.compile(r'\bcivilian harm\b|\bcivilian protection\b|\bprotection of civilians\b', re.IGNORECASE)),
    ('ceasefire diplomacy', re.compile(r'\bceasefire diplomacy\b|\bceasefire efforts?\b', re.IGNORECASE)),
    ('development finance', re.compile(r'\bdevelopment finance\b', re.IGNORECASE)),
    ('sovereign debt', re.compile(r'\bsovereign debt\b', re.IGNORECASE)),
    ('debt distress', re.compile(r'\bdebt distress\b', re.IGNORECASE)),
    ('debt restructuring', re.compile(r'\bdebt restructuring\b|\bdebt workouts?\b', re.IGNORECASE)),
    ('climate finance', re.compile(r'\bclimate finance\b', re.IGNORECASE)),
    ('political economy', re.compile(r'\bpolitical economy\b', re.IGNORECASE)),
    ('public finance', re.compile(r'\bpublic finance\b', re.IGNORECASE)),
    ('industrial policy', re.compile(r'\bindustrial policy\b', re.IGNORECASE)),
    ('green transition', re.compile(r'\bgreen transition\b|\bgreen industrialisation\b|\bgreen industrialization\b', re.IGNORECASE)),
    ('just transition', re.compile(r'\bjust transition\b', re.IGNORECASE)),
    ('multilateral lenders', re.compile(r'\bmultilateral lenders?\b', re.IGNORECASE)),
    ('IMF reform', re.compile(r'\bimf reform\b', re.IGNORECASE)),
    ('IMF negotiations', re.compile(r'\bimf negotiations?\b|\bimf programmes?\b|\bimf programs?\b', re.IGNORECASE)),
    ('IMF', re.compile(r'\bimf\b', re.IGNORECASE)),
    ('Horn of Africa', re.compile(r'\bhorn of africa\b', re.IGNORECASE)),
    ('migration routes', re.compile(r'\bmigration routes?\b', re.IGNORECASE)),
    ('border governance', re.compile(r'\bborder governance\b|\bborder policy\b|\bborder regimes?\b', re.IGNORECASE)),
    ('regional politics', re.compile(r'\bregional politics?\b|\bregional political\b', re.IGNORECASE)),
    ('Iran sanctions', re.compile(r'\biran sanctions\b|\bsanctions\b.*\biran\b|\biran\b.*\bsanctions\b', re.IGNORECASE)),
    ('post-conflict', re.compile(r'\bpost[- ]war\b|\bpost[- ]conflict\b', re.IGNORECASE)),
    ('state capacity', re.compile(r'\bstate capacity\b', re.IGNORECASE)),
]
GENERIC_STOPPHRASES = {
    'academic comment',
    'policy implications',
    'regional context',
    'current developments',
    'expert',
    'comment',
    'academic',
    'need comment',
    'need academic comment',
}
GENERIC_STOPWORDS = {
    'a', 'about', 'academic', 'across', 'an', 'and', 'are', 'around', 'as', 'at', 'be', 'by', 'comment', 'context', 'current', 'developments', 'expert', 'for', 'from', 'in', 'into', 'is', 'its', 'looking', 'need', 'of', 'on', 'or', 'regional', 'regarding', 's', 'seeking', 'the', 'their', 'this', 'through', 'to', 'up', 'with'
}
DOMAIN_WINDOW_TERMS = {
    'access', 'africa', 'asylum', 'border', 'ceasefire', 'civilians', 'civilian', 'climate', 'conflict', 'debt', 'development', 'diplomacy', 'economy', 'ethiopia', 'finance', 'forced', 'gaza', 'governance', 'green', 'horn', 'humanitarian', 'ihl', 'imf', 'industrial', 'international', 'iran', 'law', 'migration', 'middle', 'palestine', 'political', 'post', 'protection', 'public', 'refugee', 'routes', 'sanctions', 'settlement', 'sovereign', 'state', 'sudan', 'transition', 'war', 'yemen'
}
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9'&/-]+")


@dataclass(frozen=True, slots=True)
class PreparedQuery:
    normalized_subject: str
    normalized_body: str
    normalized_query: str
    keyphrases: list[str]


def _expand_abbreviations(text: str) -> str:
    expanded = text
    for pattern, replacement in ABBREVIATION_PATTERNS:
        expanded = pattern.sub(replacement, expanded)
    return expanded


def _strip_lead_in(text: str) -> str:
    stripped = text
    for pattern in LEAD_IN_PATTERNS:
        stripped = pattern.sub('', stripped)
    return stripped


def _clean_segment(text: str | None) -> str:
    cleaned = normalize_whitespace(text) or ''
    if not cleaned:
        return ''

    cleaned = _expand_abbreviations(cleaned)
    cleaned = normalize_punctuation(cleaned)
    cleaned = _expand_abbreviations(cleaned)
    cleaned = _strip_lead_in(cleaned)
    for pattern in GENERIC_TAIL_PATTERNS:
        cleaned = pattern.sub('', cleaned)
    cleaned = re.sub(r'[!?]+', ' ', cleaned)
    cleaned = re.sub(r'\band\s+and\b', 'and', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bor\s+or\b', 'or', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*[,;:]\s*', ', ', cleaned)
    cleaned = re.sub(r'(?:\s*,\s*){2,}', ', ', cleaned)
    cleaned = re.sub(r'\s*[()]\s*', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip(' ,.;:-')
    return cleaned


def _clean_phrase(text: str) -> str:
    phrase = _expand_abbreviations(normalize_punctuation(text))
    phrase = phrase.replace('?', ' ').replace('!', ' ')
    phrase = _strip_lead_in(phrase)
    phrase = re.sub(r'^["\']+|["\']+$', '', phrase)
    phrase = re.sub(r'\s+', ' ', phrase).strip(' ,.;:-')
    return phrase


def extract_keyphrases(text: str, limit: int = 8) -> list[str]:
    if not text:
        return []

    normalized_text = _clean_phrase(text)
    phrases: list[str] = []
    seen: set[str] = set()

    def add_candidate(candidate: str) -> None:
        cleaned = _clean_phrase(candidate)
        if not cleaned:
            return
        lowered = cleaned.lower()
        if lowered in GENERIC_STOPPHRASES:
            return
        tokens = [token for token in TOKEN_PATTERN.findall(cleaned) if token]
        if not tokens:
            return
        content_tokens = [token for token in tokens if token.lower() not in GENERIC_STOPWORDS]
        if not content_tokens:
            return
        if len(content_tokens) > 6:
            cleaned = ' '.join(content_tokens[:6])
            lowered = cleaned.lower()
        if lowered in seen:
            return
        seen.add(lowered)
        phrases.append(cleaned)

    for canonical_phrase, pattern in CANONICAL_PHRASES:
        if pattern.search(normalized_text):
            add_candidate(canonical_phrase)
            if len(phrases) >= limit:
                return phrases[:limit]

    fragments = re.split(r'[\.;,]|\s+-\s+', normalized_text)
    for fragment in fragments:
        fragment = fragment.strip()
        if not fragment:
            continue
        add_candidate(fragment)
        if len(phrases) >= limit:
            return phrases[:limit]

    if len(phrases) < limit:
        tokens = [token for token in TOKEN_PATTERN.findall(normalized_text) if token]
        for window_size in (2, 3):
            for index in range(len(tokens) - window_size + 1):
                window = tokens[index : index + window_size]
                lowered_window = [token.lower() for token in window]
                if any(token in GENERIC_STOPWORDS for token in lowered_window):
                    continue
                if not any(token in DOMAIN_WINDOW_TERMS for token in lowered_window):
                    continue
                add_candidate(' '.join(window))
                if len(phrases) >= limit:
                    return phrases[:limit]

    if not phrases:
        tokens = [
            token
            for token in TOKEN_PATTERN.findall(normalized_text)
            if token.lower() not in GENERIC_STOPWORDS and len(token) > 2
        ]
        for token in tokens:
            add_candidate(token)
            if len(phrases) >= limit:
                break

    return phrases[:limit]


def prepare_enquiry_query(subject: str, body: str) -> PreparedQuery:
    normalized_subject = _clean_segment(subject)
    normalized_body = _clean_segment(body)

    if normalized_subject and normalized_body and normalized_body.lower().startswith(normalized_subject.lower()):
        normalized_query = normalized_body
    else:
        normalized_query = '. '.join(part for part in [normalized_subject, normalized_body] if part)

    normalized_query = re.sub(r'\s+', ' ', normalized_query).strip(' .')
    keyphrases = extract_keyphrases(normalized_query)

    return PreparedQuery(
        normalized_subject=normalized_subject,
        normalized_body=normalized_body,
        normalized_query=normalized_query,
        keyphrases=keyphrases,
    )

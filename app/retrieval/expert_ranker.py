from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
import re


FAIRNESS_PENALTY_REPEAT = 0.05
MIN_SINGLE_CHUNK_SCORE = 0.55
MIN_FINAL_SCORE = 0.62
EVIDENCE_BACKED_SINGLE_CHUNK_FLOOR = 0.44
SECTION_WEIGHTS = {
    'research_interests': 1.0,
    'biography': 0.75,
    'publications': 0.35,
}
PHRASE_MATCH_BONUS = 0.12
PHRASE_MATCH_CAP = 0.24
LOOSE_PHRASE_MATCH_BONUS = 0.06
LOOSE_PHRASE_MATCH_CAP = 0.12
UNIGRAM_MATCH_BONUS = 0.03
UNIGRAM_MATCH_CAP = 0.12
PUBLICATION_ONLY_PENALTY = 0.12
WEAK_PUBLICATION_BEST_PENALTY = 0.08
MEDIA_SIGNAL_TERMS = [
    'media',
    'comment',
    'comments',
    'commentary',
    'public engagement',
    'advised',
    'interview',
    'broadcast',
    'press',
]
GENERIC_QUERY_TERMS = {
    'academic',
    'comment',
    'developments',
    'expert',
    'implications',
    'policy',
    'regional',
}
OVERLAP_STOPWORDS = {
    'a',
    'about',
    'academic',
    'across',
    'an',
    'and',
    'are',
    'around',
    'as',
    'at',
    'be',
    'by',
    'comment',
    'context',
    'current',
    'developments',
    'expert',
    'for',
    'from',
    'in',
    'into',
    'is',
    'its',
    'local',
    'looking',
    'need',
    'of',
    'on',
    'or',
    'regional',
    'regarding',
    's',
    'seeking',
    'the',
    'their',
    'this',
    'through',
    'to',
    'up',
    'with',
}
MIN_OVERRIDE_UNIGRAM_MATCHES = 2
HIGH_SIGNAL_FINAL_SCORE_FLOOR = 0.52
HIGH_SIGNAL_QUERY_PHRASES = {
    'civilian harm',
    'climate finance',
    'development finance',
    'debt distress',
    'debt restructuring',
    'ethiopia',
    'gaza',
    'green transition',
    'horn of africa',
    'humanitarian access',
    'imf',
    'imf negotiations',
    'imf reform',
    'industrial policy',
    'international law',
    'iran',
    'iran sanctions',
    'migration routes',
    'regional politics',
    'sudan',
    'sovereign debt',
    'yemen',
}


@dataclass(frozen=True, slots=True)
class RankerConfig:
    enable_topic_boosts: bool = True
    enable_media_signal_boost: bool = False
    enable_diversity_penalty: bool = False
    min_single_chunk_score: float = MIN_SINGLE_CHUNK_SCORE
    min_final_score: float = MIN_FINAL_SCORE


DEFAULT_RANKER_CONFIG = RankerConfig()


def _normalize(text: str | None) -> str:
    if not text:
        return ''
    return re.sub(r'\s+', ' ', str(text)).strip().lower()


def _word_tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", _normalize(text))


def _fallback_keyphrases(query_text: str, topic_labels: list[str] | None = None) -> list[str]:
    phrases: list[str] = []
    seen: set[str] = set()
    for candidate in [query_text, *(topic_labels or [])]:
        normalized = _normalize(candidate)
        if not normalized:
            continue
        parts = re.split(r'[;,]', normalized)
        for part in parts:
            cleaned = part.strip(' .:-')
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            phrases.append(cleaned)
    return phrases[:8]


def _section_weight(section: str | None) -> float:
    return SECTION_WEIGHTS.get((section or '').lower(), 0.50)


def _compute_media_signal_boost(expert: dict) -> float:
    searchable_text = _normalize(' '.join(chunk.get('text', '') for chunk in expert.get('supporting_chunks', [])))
    for term in MEDIA_SIGNAL_TERMS:
        if term in searchable_text:
            return 0.05
    return 0.0


def _truncate_title(title: str | None, max_len: int = 140) -> str | None:
    if not title:
        return None
    title = re.sub(r'\s+', ' ', title).strip()
    if len(title) <= max_len:
        return title
    return title[: max_len - 1].rstrip() + '...'


def _confidence_label(final_score: float, best_adjusted_score: float, overlap_terms: list[str]) -> str:
    if final_score >= 0.9 and (best_adjusted_score >= 0.68 or overlap_terms):
        return 'High'
    if final_score >= 0.68 and best_adjusted_score >= 0.5:
        return 'Medium'
    return 'Low'


def _token_present_in_text(token: str, searchable_text: str) -> bool:
    return bool(re.search(rf'\b{re.escape(token)}\b', searchable_text))


def _match_overlap_terms(expert: dict, keyphrases: list[str]) -> tuple[float, list[str], list[str], list[str]]:
    searchable_parts = [
        expert.get('name') or '',
        expert.get('title') or '',
        expert.get('department') or '',
        ' '.join(expert.get('topics', []) or []),
    ]
    for chunk in expert.get('supporting_chunks', []):
        searchable_parts.extend(
            [
                chunk.get('text') or '',
                chunk.get('section') or '',
                ' '.join(chunk.get('topics', []) or []),
            ]
        )
    searchable_text = _normalize(' '.join(searchable_parts))

    exact_phrase_matches: list[str] = []
    loose_phrase_matches: list[str] = []
    phrase_bonus = 0.0
    loose_phrase_bonus = 0.0
    matched_unigrams: set[str] = set()

    for phrase in keyphrases:
        normalized_phrase = _normalize(phrase)
        if not normalized_phrase:
            continue
        phrase_tokens = [
            token
            for token in _word_tokens(normalized_phrase)
            if token not in GENERIC_QUERY_TERMS and token not in OVERLAP_STOPWORDS
        ]
        if not phrase_tokens:
            continue
        if len(phrase_tokens) > 1 and normalized_phrase in searchable_text:
            exact_phrase_matches.append(phrase)
            phrase_bonus += PHRASE_MATCH_BONUS
            matched_unigrams.update(phrase_tokens)
            continue
        if len(phrase_tokens) > 1 and all(_token_present_in_text(token, searchable_text) for token in phrase_tokens):
            loose_phrase_matches.append(phrase)
            loose_phrase_bonus += LOOSE_PHRASE_MATCH_BONUS
            matched_unigrams.update(phrase_tokens)

    phrase_bonus = min(phrase_bonus, PHRASE_MATCH_CAP)
    loose_phrase_bonus = min(loose_phrase_bonus, LOOSE_PHRASE_MATCH_CAP)

    additional_unigram_matches: list[str] = []
    for phrase in keyphrases:
        for token in _word_tokens(phrase):
            if token in GENERIC_QUERY_TERMS or token in OVERLAP_STOPWORDS or token in matched_unigrams or len(token) < 3:
                continue
            if _token_present_in_text(token, searchable_text):
                matched_unigrams.add(token)
                additional_unigram_matches.append(token)

    unigram_bonus = min(len(additional_unigram_matches) * UNIGRAM_MATCH_BONUS, UNIGRAM_MATCH_CAP)
    return phrase_bonus + loose_phrase_bonus + unigram_bonus, exact_phrase_matches, loose_phrase_matches, additional_unigram_matches



def _has_high_signal_query_alignment(
    query_keyphrases: list[str],
    exact_phrase_matches: list[str],
    loose_phrase_matches: list[str],
    unigram_matches: list[str],
) -> bool:
    high_signal_phrases = {
        normalized
        for phrase in query_keyphrases
        for normalized in [_normalize(phrase)]
        if normalized in HIGH_SIGNAL_QUERY_PHRASES
    }
    if len(high_signal_phrases) < 2:
        return False

    query_tokens: set[str] = set()
    for phrase in high_signal_phrases:
        query_tokens.update(
            token
            for token in _word_tokens(phrase)
            if token not in OVERLAP_STOPWORDS and token not in GENERIC_QUERY_TERMS
        )

    matched_tokens: set[str] = set(
        token
        for token in unigram_matches
        if token not in OVERLAP_STOPWORDS and token not in GENERIC_QUERY_TERMS
    )
    for phrase in [*exact_phrase_matches, *loose_phrase_matches]:
        matched_tokens.update(
            token
            for token in _word_tokens(phrase)
            if token not in OVERLAP_STOPWORDS and token not in GENERIC_QUERY_TERMS
        )

    return len(query_tokens & matched_tokens) >= 2

def _weak_evidence_penalty(expert: dict, exact_phrase_matches: list[str], loose_phrase_matches: list[str]) -> float:
    supporting_chunks = expert.get('supporting_chunks', [])
    if not supporting_chunks:
        return 0.0

    sections = {chunk.get('section') for chunk in supporting_chunks}
    penalty = 0.0
    if sections == {'publications'}:
        penalty -= PUBLICATION_ONLY_PENALTY
    if supporting_chunks[0].get('section') == 'publications' and not (exact_phrase_matches or loose_phrase_matches):
        penalty -= WEAK_PUBLICATION_BEST_PENALTY
    return penalty


def _make_rationale(expert: dict, exact_phrase_matches: list[str], loose_phrase_matches: list[str], unigram_matches: list[str]) -> str:
    section_labels = ', '.join(sorted({chunk['section'] for chunk in expert['supporting_chunks']}))
    overlap_parts: list[str] = []
    if exact_phrase_matches:
        overlap_parts.append(f"exact query phrase matches: {', '.join(exact_phrase_matches[:2])}")
    if loose_phrase_matches:
        overlap_parts.append(f"concept-level query alignment: {', '.join(loose_phrase_matches[:2])}")
    if unigram_matches:
        overlap_parts.append(f"key term overlap: {', '.join(unigram_matches[:4])}")

    if overlap_parts:
        overlap_text = ' Alignment observed through ' + '; '.join(overlap_parts) + '.'
    else:
        overlap_text = ''

    return (
        f'Matched on retrieved evidence from {section_labels}.{overlap_text} '
        'Recommendation is grounded in profile content and should be reviewed by staff before outreach.'
    )


def ranker_config_to_dict(config: RankerConfig | None) -> dict[str, bool | float]:
    return asdict(config or DEFAULT_RANKER_CONFIG)


def rank_experts(
    chunks: list[dict],
    top_k: int = 5,
    query_text: str = '',
    topic_labels: list[str] | None = None,
    query_keyphrases: list[str] | None = None,
    config: RankerConfig | None = None,
) -> list[dict]:
    resolved_config = config or DEFAULT_RANKER_CONFIG
    grouped: dict[str, dict] = defaultdict(
        lambda: {
            'profile_id': '',
            'name': '',
            'title': None,
            'department': None,
            'source_url': '',
            'supporting_chunks': [],
            'hit_count': 0,
            'topics': [],
        }
    )

    for chunk in chunks:
        pid = chunk['profile_id']
        item = grouped[pid]
        item['profile_id'] = pid
        item['name'] = chunk['name']
        item['title'] = chunk.get('title')
        item['department'] = chunk.get('department')
        item['source_url'] = chunk['source_url']
        item['hit_count'] += 1

        chunk_topics = chunk.get('topics') or []
        if chunk_topics:
            existing = set(item['topics'])
            for topic in chunk_topics:
                if topic not in existing:
                    item['topics'].append(topic)
                    existing.add(topic)

        adjusted_chunk = dict(chunk)
        adjusted_chunk['adjusted_score'] = round(chunk['score'] * _section_weight(chunk.get('section')), 4)
        item['supporting_chunks'].append(adjusted_chunk)

    keyphrases = query_keyphrases or _fallback_keyphrases(query_text, topic_labels)
    ranked = []

    for expert in grouped.values():
        sorted_chunks = sorted(
            expert['supporting_chunks'],
            key=lambda chunk: (chunk['adjusted_score'], chunk['score']),
            reverse=True,
        )
        retained_chunks = sorted_chunks[:3]
        expert['supporting_chunks'] = retained_chunks

        chunk_scores = [chunk['adjusted_score'] for chunk in retained_chunks]
        best_score = chunk_scores[0] if chunk_scores else 0.0
        second_score = chunk_scores[1] if len(chunk_scores) > 1 else 0.0
        third_score = chunk_scores[2] if len(chunk_scores) > 2 else 0.0
        best_raw_chunk_score = max((chunk['score'] for chunk in retained_chunks), default=0.0)
        expert_evidence_score = best_score + (0.35 * second_score) + (0.15 * third_score)

        overlap_bonus = 0.0
        exact_phrase_matches: list[str] = []
        loose_phrase_matches: list[str] = []
        unigram_matches: list[str] = []
        if resolved_config.enable_topic_boosts:
            overlap_bonus, exact_phrase_matches, loose_phrase_matches, unigram_matches = _match_overlap_terms(expert, keyphrases)

        media_boost = _compute_media_signal_boost(expert) if resolved_config.enable_media_signal_boost else 0.0
        penalty = _weak_evidence_penalty(expert, exact_phrase_matches, loose_phrase_matches)

        final_score = expert_evidence_score + overlap_bonus + media_boost + penalty
        diversity_note = None
        if resolved_config.enable_diversity_penalty and expert['hit_count'] > 3:
            final_score -= FAIRNESS_PENALTY_REPEAT
            diversity_note = 'Small penalty applied to reduce concentration on repeated chunk hits.'

        strong_overlap_override = (
            bool(retained_chunks)
            and retained_chunks[0].get('section') != 'publications'
            and best_raw_chunk_score >= EVIDENCE_BACKED_SINGLE_CHUNK_FLOOR
            and (
                bool(exact_phrase_matches)
                or bool(loose_phrase_matches)
                or len(unigram_matches) >= MIN_OVERRIDE_UNIGRAM_MATCHES
            )
        )
        high_signal_final_override = (
            strong_overlap_override
            and _has_high_signal_query_alignment(
                keyphrases,
                exact_phrase_matches,
                loose_phrase_matches,
                unigram_matches,
            )
            and final_score >= HIGH_SIGNAL_FINAL_SCORE_FLOOR
        )

        if not (
            (
                expert['hit_count'] >= 2
                or best_raw_chunk_score >= resolved_config.min_single_chunk_score
                or strong_overlap_override
            )
            and (
                final_score >= resolved_config.min_final_score
                or high_signal_final_override
            )
        ):
            continue

        expert['final_score'] = round(final_score, 4)
        expert['title'] = _truncate_title(expert.get('title'))
        expert['confidence'] = _confidence_label(
            expert['final_score'],
            best_score,
            exact_phrase_matches + loose_phrase_matches + unigram_matches,
        )
        expert['rationale'] = _make_rationale(expert, exact_phrase_matches, loose_phrase_matches, unigram_matches)
        expert['diversity_note'] = diversity_note
        ranked.append(expert)

    ranked.sort(key=lambda expert: expert['final_score'], reverse=True)
    return ranked[:top_k]




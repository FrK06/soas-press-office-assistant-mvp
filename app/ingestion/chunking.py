from __future__ import annotations

import re
from typing import Iterable

from app.config import settings
from app.schemas import ProfileChunk, ProfileDocument
from app.utils.text_cleaning import contains_meaningful_publication_text, normalize_punctuation, normalize_whitespace


SECTION_ORDER = [
    'research_interests',
    'biography',
    'publications',
]


def normalize_text(text: str) -> str:
    normalized = normalize_whitespace(text) or ''
    normalized = normalize_punctuation(normalized)
    normalized = normalized.replace('\n\n', '\n')
    normalized = re.sub(r'\s+', ' ', normalized.replace('\n', ' ')).strip()
    return normalized


def sentence_split(text: str) -> list[str]:
    text = normalize_text(text)
    if not text:
        return []

    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def simple_chunk_text(text: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
    chunk_size = chunk_size or settings.max_chunk_chars
    overlap = overlap or settings.chunk_overlap_chars

    sentences = sentence_split(text)
    if not sentences:
        return []

    chunks: list[str] = []
    current = ''
    for sentence in sentences:
        candidate = sentence if not current else f'{current} {sentence}'
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current.strip())

        if len(sentence) > chunk_size:
            words = sentence.split()
            piece = ''
            for word in words:
                next_piece = word if not piece else f'{piece} {word}'
                if len(next_piece) <= chunk_size:
                    piece = next_piece
                else:
                    if piece:
                        chunks.append(piece.strip())
                    piece = word
            current = piece.strip()
        else:
            current = sentence

    if current:
        chunks.append(current.strip())

    if overlap <= 0 or len(chunks) <= 1:
        return chunks

    overlapped: list[str] = [chunks[0]]
    for index in range(1, len(chunks)):
        prev = chunks[index - 1]
        curr = chunks[index]
        tail = prev[-overlap:].strip()
        if tail and not curr.startswith(tail):
            merged = f'{tail} {curr}'.strip()
            overlapped.append(merged[: chunk_size + overlap])
        else:
            overlapped.append(curr)
    return overlapped


def publication_chunk_text(text: str) -> list[str]:
    normalized = normalize_whitespace(text) or ''
    if not normalized:
        return []

    pieces = [piece.strip() for piece in re.split(r'\n+|;\s+', normalized) if piece.strip()]
    return pieces or [normalized]


def iter_profile_sections(profile: ProfileDocument) -> Iterable[tuple[str, str]]:
    for section in SECTION_ORDER:
        value = getattr(profile, section, None)
        if value:
            yield section, value


def _keep_chunk(section: str, text: str) -> bool:
    if section != 'publications':
        return True
    return contains_meaningful_publication_text(text)


def _section_pieces(section: str, text: str) -> list[str]:
    if section == 'publications':
        return publication_chunk_text(text)
    return simple_chunk_text(text)


def build_chunks(profile: ProfileDocument) -> list[ProfileChunk]:
    chunks: list[ProfileChunk] = []
    index = 0

    for section, text in iter_profile_sections(profile):
        for piece in _section_pieces(section, text):
            raw_piece = normalize_whitespace(piece) or ''
            if not raw_piece or not _keep_chunk(section, raw_piece):
                continue

            cleaned_piece = normalize_text(raw_piece)
            if not cleaned_piece:
                continue

            index += 1
            chunks.append(
                ProfileChunk(
                    chunk_id=f'{profile.profile_id}-chunk-{index}',
                    profile_id=profile.profile_id,
                    name=profile.name,
                    department=profile.department,
                    title=profile.title,
                    topics=profile.expertise_topics,
                    section=section,
                    text=cleaned_piece,
                    source_url=profile.source_url,
                    last_checked=profile.last_checked,
                    content_hash=profile.content_hash,
                )
            )

    return chunks

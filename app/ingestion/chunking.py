from __future__ import annotations

import re
from typing import Iterable

from app.config import settings
from app.schemas import ProfileChunk, ProfileDocument


SECTION_ORDER = [
    "biography",
    "research_interests",
    "publications",
]


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    return text


def sentence_split(text: str) -> list[str]:
    text = normalize_text(text)
    if not text:
        return []

    # Preserve paragraph boundaries a little better
    text = text.replace("\n", " ")

    # Split on sentence endings followed by whitespace
    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences


def simple_chunk_text(text: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
    chunk_size = chunk_size or settings.max_chunk_chars
    overlap = overlap or settings.chunk_overlap_chars

    sentences = sentence_split(text)
    if not sentences:
        return []

    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        candidate = sentence if not current else f"{current} {sentence}"

        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current.strip())

        # If a single sentence is too long, fall back to word-safe splitting
        if len(sentence) > chunk_size:
            words = sentence.split()
            piece = ""
            for word in words:
                next_piece = word if not piece else f"{piece} {word}"
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

    # Soft overlap: prepend the tail of the previous chunk to the next one
    overlapped: list[str] = [chunks[0]]
    for i in range(1, len(chunks)):
        prev = chunks[i - 1]
        curr = chunks[i]

        tail = prev[-overlap:].strip()
        if tail and not curr.startswith(tail):
            merged = f"{tail} {curr}".strip()
            overlapped.append(merged[: chunk_size + overlap])
        else:
            overlapped.append(curr)

    return overlapped


def iter_profile_sections(profile: ProfileDocument) -> Iterable[tuple[str, str]]:
    for section in SECTION_ORDER:
        value = getattr(profile, section, None)
        if value:
            yield section, value


def build_chunks(profile: ProfileDocument) -> list[ProfileChunk]:
    chunks: list[ProfileChunk] = []
    index = 0

    for section, text in iter_profile_sections(profile):
        for piece in simple_chunk_text(text):
            cleaned_piece = normalize_text(piece)
            if not cleaned_piece:
                continue

            index += 1
            chunks.append(
                ProfileChunk(
                    chunk_id=f"{profile.profile_id}-chunk-{index}",
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
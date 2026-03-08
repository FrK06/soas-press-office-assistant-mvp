from __future__ import annotations

from collections import defaultdict
import re


FAIRNESS_PENALTY_REPEAT = 0.05
MIN_SINGLE_CHUNK_SCORE = 0.60
MIN_FINAL_SCORE = 0.62

TOPIC_BOOSTS = {
    "migration": 0.18,
    "displacement": 0.14,
    "refugee": 0.14,
    "asylum": 0.14,
    "middle east": 0.16,
    "gaza": 0.10,
    "border": 0.12,
    "diaspora": 0.08,
    "humanitarian": 0.08,
}

MEDIA_SIGNAL_TERMS = [
    "media",
    "comment",
    "comments",
    "commentary",
    "public engagement",
    "advised",
    "interview",
    "broadcast",
    "press",
]


def _normalize(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip().lower()


def _extract_terms(query_text: str, topic_labels: list[str] | None = None) -> set[str]:
    text = _normalize(query_text)
    terms = set()

    for candidate in TOPIC_BOOSTS.keys():
        if candidate in text:
            terms.add(candidate)

    for label in topic_labels or []:
        label_norm = _normalize(label)
        if label_norm:
            terms.add(label_norm)

    return terms


def _compute_topic_boost(expert: dict, query_terms: set[str]) -> float:
    searchable_parts = [
        expert.get("name"),
        expert.get("title"),
        expert.get("department"),
        " ".join(expert.get("topics", []) or []),
    ]

    for chunk in expert.get("supporting_chunks", []):
        searchable_parts.extend(
            [
                chunk.get("text"),
                chunk.get("section"),
                " ".join(chunk.get("topics", []) or []),
            ]
        )

    searchable_text = _normalize(" ".join([p for p in searchable_parts if p]))

    boost = 0.0
    for term in query_terms:
        if term in searchable_text:
            boost += TOPIC_BOOSTS.get(term, 0.0)

    return boost


def _compute_media_signal_boost(expert: dict) -> float:
    searchable_text = _normalize(
        " ".join(chunk.get("text", "") for chunk in expert.get("supporting_chunks", []))
    )

    for term in MEDIA_SIGNAL_TERMS:
        if term in searchable_text:
            return 0.05
    return 0.0


def _truncate_title(title: str | None, max_len: int = 140) -> str | None:
    if not title:
        return None
    title = re.sub(r"\s+", " ", title).strip()
    if len(title) <= max_len:
        return title
    return title[: max_len - 1].rstrip() + "…"


def _confidence_label(final_score: float, hit_count: int, best_chunk_score: float) -> str:
    if final_score >= 1.2 and (hit_count >= 2 or best_chunk_score >= 0.72):
        return "High"
    if final_score >= 0.8 and (hit_count >= 1 or best_chunk_score >= 0.62):
        return "Medium"
    return "Low"


def _make_rationale(expert: dict, matched_terms: list[str]) -> str:
    section_labels = ", ".join(sorted({c["section"] for c in expert["supporting_chunks"]}))
    if matched_terms:
        return (
            f"Matched on retrieved evidence from {section_labels}. "
            f"Boosted by overlap with enquiry themes: {', '.join(matched_terms)}. "
            f"Recommendation is grounded in profile content and should be reviewed by staff before outreach."
        )
    return (
        f"Matched on retrieved evidence from {section_labels}. "
        f"Recommendation is grounded in profile content and should be reviewed by staff before outreach."
    )


def rank_experts(
    chunks: list[dict],
    top_k: int = 5,
    query_text: str = "",
    topic_labels: list[str] | None = None,
) -> list[dict]:
    grouped: dict[str, dict] = defaultdict(
        lambda: {
            "profile_id": "",
            "name": "",
            "title": None,
            "department": None,
            "source_url": "",
            "final_score": 0.0,
            "supporting_chunks": [],
            "hit_count": 0,
            "topics": [],
        }
    )

    for chunk in chunks:
        pid = chunk["profile_id"]
        item = grouped[pid]
        item["profile_id"] = pid
        item["name"] = chunk["name"]
        item["title"] = chunk.get("title")
        item["department"] = chunk.get("department")
        item["source_url"] = chunk["source_url"]
        item["final_score"] += chunk["score"]
        item["supporting_chunks"].append(chunk)
        item["hit_count"] += 1

        chunk_topics = chunk.get("topics") or []
        if chunk_topics:
            existing = set(item["topics"])
            for topic in chunk_topics:
                if topic not in existing:
                    item["topics"].append(topic)
                    existing.add(topic)

    query_terms = _extract_terms(query_text, topic_labels)

    ranked = []
    for expert in grouped.values():
        expert["supporting_chunks"] = sorted(
            expert["supporting_chunks"],
            key=lambda x: x["score"],
            reverse=True,
        )[:3]

        best_chunk_score = max((c["score"] for c in expert["supporting_chunks"]), default=0.0)

        topic_boost = _compute_topic_boost(expert, query_terms)
        media_boost = _compute_media_signal_boost(expert)
        expert["final_score"] += topic_boost + media_boost

        matched_terms = []
        searchable_text = _normalize(
            " ".join(
                [
                    expert.get("title") or "",
                    expert.get("department") or "",
                    " ".join(expert.get("topics", []) or []),
                    " ".join(c.get("text", "") for c in expert["supporting_chunks"]),
                ]
            )
        )
        for term in sorted(query_terms):
            if term in searchable_text:
                matched_terms.append(term)

        if expert["hit_count"] > 3:
            expert["final_score"] -= FAIRNESS_PENALTY_REPEAT
            expert["diversity_note"] = "Small penalty applied to reduce concentration on repeated chunk hits."
        else:
            expert["diversity_note"] = None

        expert["title"] = _truncate_title(expert.get("title"))
        expert["confidence"] = _confidence_label(
            final_score=expert["final_score"],
            hit_count=expert["hit_count"],
            best_chunk_score=best_chunk_score,
        )
        expert["rationale"] = _make_rationale(expert, matched_terms)

        if not (
            (expert["hit_count"] >= 2 or best_chunk_score >= MIN_SINGLE_CHUNK_SCORE)
            and expert["final_score"] >= MIN_FINAL_SCORE
        ):
            continue

        ranked.append(expert)

    ranked.sort(key=lambda x: x["final_score"], reverse=True)
    return ranked[:top_k]
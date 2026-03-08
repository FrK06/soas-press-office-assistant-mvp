from __future__ import annotations

from app.llm.client import get_openai_client
from app.llm.prompts import RECOMMENDATION_PROMPT


def generate_staff_summary(enquiry_text: str, experts: list[dict]) -> str:
    evidence_parts: list[str] = []
    for idx, expert in enumerate(experts, start=1):
        evidence_parts.append(f'Expert {idx}: {expert["name"]} | {expert.get("title", "")} | {expert.get("department", "")}')
        for chunk in expert['supporting_chunks']:
            evidence_parts.append(f'- Source URL: {chunk["source_url"]}')
            evidence_parts.append(f'- Section: {chunk["section"]}')
            evidence_parts.append(f'- Evidence: {chunk["text"]}')

    prompt = RECOMMENDATION_PROMPT.format(
        enquiry=enquiry_text,
        evidence='\n'.join(evidence_parts),
    )

    client = get_openai_client()
    response = client.responses.create(model='gpt-4.1-mini', input=prompt)
    return response.output_text

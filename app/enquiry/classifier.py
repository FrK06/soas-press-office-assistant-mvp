from __future__ import annotations

TOPIC_KEYWORDS = {
    'Middle East': ['middle east', 'gaza', 'iran', 'iraq', 'israel', 'palestine', 'syria'],
    'Africa': ['africa', 'sudan', 'ethiopia', 'nigeria', 'kenya', 'ghana'],
    'Migration': ['migration', 'asylum', 'refugee', 'diaspora', 'border'],
    'Religion': ['religion', 'faith', 'islam', 'christianity', 'buddhism', 'hinduism'],
    'China': ['china', 'beijing', 'xinjiang', 'taiwan'],
    'Gender': ['gender', 'women', 'feminism', 'masculinity'],
    'Development': ['development', 'aid', 'humanitarian', 'global south'],
    'Politics': ['election', 'government', 'parliament', 'policy', 'politics'],
}


def classify_enquiry(subject: str, body: str) -> list[str]:
    text = f'{subject}\n{body}'.lower()
    labels = [label for label, words in TOPIC_KEYWORDS.items() if any(word in text for word in words)]
    return labels or ['General']

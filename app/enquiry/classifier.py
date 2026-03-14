from __future__ import annotations

import re


TOPIC_PATTERNS = {
    'Middle East': (
        r'\bmiddle east\b',
        r'\bgaza\b',
        r'\biran\b',
        r'\biraq\b',
        r'\bisrael\b',
        r'\bpalestine\b',
        r'\bsyria\b',
    ),
    'Africa': (
        r'\bafrica\b',
        r'\bsudan\b',
        r'\bethiopia\b',
        r'\bnigeria\b',
        r'\bkenya\b',
        r'\bghana\b',
    ),
    'Migration': (
        r'\bmigration\b',
        r'\basylum\b',
        r'\brefugee\b',
        r'\bdiaspora\b',
        r'\bborder\b',
        r'\bdisplacement\b',
        r'\bforced migration\b',
    ),
    'Religion': (
        r'\breligion\b',
        r'\bfaith\b',
        r'\bislam\b',
        r'\bchristianity\b',
        r'\bbuddhism\b',
        r'\bhinduism\b',
    ),
    'China': (
        r'\bchina\b',
        r'\bbeijing\b',
        r'\bxinjiang\b',
        r'\btaiwan\b',
    ),
    'Gender': (
        r'\bgender\b',
        r'\bwomen\b',
        r'\bfeminism\b',
        r'\bmasculinity\b',
        r'\bsexuality\b',
    ),
    'Development': (
        r'\baid\b',
        r'\bhumanitarian\b',
        r'\bglobal south\b',
        r'\beconomic development\b',
        r'\binternational development\b',
        r'\bdevelopment economics\b',
        r'\bdevelopment studies\b',
        r'\bsustainable development\b',
        r'\bdevelopment finance\b',
        r'\bdevelopment partnerships\b',
    ),
    'Politics': (
        r'\belection\b',
        r'\bgovernment\b',
        r'\bparliament\b',
        r'\bpolitics\b',
        r'\bgovernance\b',
        r'\bpolitical economy\b',
        r'\bpolitical ecology\b',
        r'\bpublic policy\b',
        r'\bindustrial policy\b',
        r'\btrade policy\b',
        r'\bregulatory governance\b',
        r'\bregulation\b',
    ),
}


def classify_enquiry(subject: str, body: str) -> list[str]:
    text = re.sub(r'\s+', ' ', f'{subject}\n{body}').strip().lower()
    labels = [
        label
        for label, patterns in TOPIC_PATTERNS.items()
        if any(re.search(pattern, text) for pattern in patterns)
    ]
    return labels or ['General']

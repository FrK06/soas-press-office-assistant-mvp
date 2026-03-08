from __future__ import annotations

import json
from pathlib import Path

from app.schemas import ProfileDocument


PROCESSED_DIR = Path('data/processed_profiles')


def load_processed_profiles(directory: Path | None = None) -> list[ProfileDocument]:
    directory = directory or PROCESSED_DIR
    profiles: list[ProfileDocument] = []
    for path in sorted(directory.glob('*.json')):
        profiles.append(ProfileDocument.model_validate(json.loads(path.read_text(encoding='utf-8'))))
    return profiles

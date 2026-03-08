from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from app.schemas import ProfileDocument
from app.utils.dates import utcnow_iso
from app.utils.hashing import sha256_text


OUTPUT_DIR = Path('data/processed_profiles')


def extract_text(soup: BeautifulSoup, selectors: list[str]) -> str:
    parts: list[str] = []
    for selector in selectors:
        for node in soup.select(selector):
            text = ' '.join(node.get_text(' ', strip=True).split())
            if text:
                parts.append(text)
    return '\n'.join(dict.fromkeys(parts))


def scrape_profile(url: str) -> ProfileDocument:
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    name = (soup.select_one('h1') or soup.select_one('title')).get_text(strip=True)
    biography = extract_text(soup, ['section p', 'article p', '.biography p'])
    research = extract_text(soup, ['.research-interests p', '.research p'])
    title = None
    department = None
    topics: list[str] = []
    combined = '\n'.join([name, biography, research])

    profile_id = 'soas-' + '-'.join(name.lower().replace("'", '').split())
    content_hash = sha256_text(combined)

    return ProfileDocument(
        profile_id=profile_id,
        name=name,
        title=title,
        department=department,
        expertise_topics=topics,
        biography=biography or None,
        research_interests=research or None,
        publications=None,
        source_url=url,
        last_checked=utcnow_iso(),
        content_hash=content_hash,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('urls', nargs='+')
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for url in args.urls:
        profile = scrape_profile(url)
        out_path = OUTPUT_DIR / f'{profile.profile_id}.json'
        out_path.write_text(profile.model_dump_json(indent=2), encoding='utf-8')
        print(f'Wrote {out_path}')


if __name__ == '__main__':
    main()

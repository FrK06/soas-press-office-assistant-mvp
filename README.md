# SOAS Press Office Assistant

A production-shaped MVP for a grounded, approval-gated RAG system that recommends academic experts for media enquiries.

## What it does

- ingests controlled profile documents
- chunks and embeds profile content into ChromaDB
- classifies incoming media enquiries
- verifies media senders using a proportionate ruleset
- retrieves and ranks 3 to 5 experts with source evidence
- logs each enquiry for audit
- records staff approval decisions before any outreach

## Project structure

```text
app/
  main.py
  config.py
  schemas.py
  db.py
  ingestion/
  retrieval/
  enquiry/
  llm/
  utils/
data/processed_profiles/
tests/
```

## Quick start

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Add your API key to `.env` if you want live embeddings and optional LLM summaries.

### 4. Index the demo profiles

From the project root:

```bash
python -m app.ingestion.upsert_chroma
```

### 5. Run the API

```bash
uvicorn app.main:app --reload
```

### 6. Test the API

Open the docs at `/docs` or send a request:

```bash
curl -X POST http://127.0.0.1:8000/enquiries/process \
  -H "Content-Type: application/json" \
  -d '{
    "sender_name": "Jane Reporter",
    "sender_email": "jane@bbc.co.uk",
    "outlet_name": "BBC News",
    "subject": "Need an expert on migration and Gaza",
    "body": "Looking for an academic comment on displacement, migration governance, and regional political implications."
  }'
```

## Example response shape

The system returns:

- verification result
- topic labels
- recommended experts
- supporting evidence chunks
- approval flag
- optional LLM staff summary

## Approval endpoint

```bash
curl -X POST http://127.0.0.1:8000/enquiries/approval \
  -H "Content-Type: application/json" \
  -d '{
    "enquiry_id": "paste-id-here",
    "decision": "approved",
    "reviewer_name": "Press Officer",
    "notes": "Proceed with manual outreach."
  }'
```

## Notes for Task 2

This MVP is intentionally simple but assessment-friendly:

- grounded outputs only
- no automated outreach
- approval gate is explicit
- manual handling route exists
- audit logging is built in
- profile refresh can be supported using `last_checked` and `content_hash`

## Recommended next improvements

1. Replace keyword classification with constrained LLM classification.
2. Add structured metadata filters for language, region, and department.
3. Add freshness checks and profile re-crawling.
4. Add a reranker model or hybrid BM25 + vector retrieval.
5. Add fairness analytics to detect concentration on the same academics.
6. Add a small frontend for press staff review.

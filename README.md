# SOAS Press Office Assistant MVP

A grounded, approval-gated Retrieval-Augmented Generation (RAG) prototype for matching media enquiries to relevant academic experts using SOAS-controlled profile data.

This MVP was designed as a practical proof of concept for a press-office workflow where staff need faster, more consistent, and more transparent expert matching, while retaining human oversight before any outreach takes place.

## Overview

SOAS External Communications currently handles media enquiries through manual triage. This MVP explores how a RAG-based assistant could support that process by:

- capturing and processing incoming media enquiries
- applying proportionate sender verification rules
- retrieving relevant profile evidence from academic data
- recommending 3–5 suitable experts with source support
- generating a staff-facing summary
- requiring explicit staff approval before outreach
- logging decisions for audit and reporting

The system is intentionally staff-facing. It does not contact academics automatically and does not generate ungrounded recommendations.

## Key features

- **Grounded retrieval** from structured academic profile content
- **Approval-gated workflow** before any outreach
- **Media verification rules** for recognised outlets and manual fallback cases
- **Expert ranking** using semantic retrieval plus topic-aware boosting
- **Evidence-linked recommendations** with supporting chunks and source URLs
- **Staff summary generation** for quick internal review
- **Audit logging** for enquiries and approval decisions
- **Excel-to-JSON ingestion pipeline** for profile data preparation

## Current architecture
```text
Enquiry intake
→ Sender verification
→ Topic classification
→ Semantic retrieval
→ Expert aggregation and ranking
→ Staff-facing summary
→ Approval decision logging
```

## Repository structure
```
app/
  main.py
  config.py
  schemas.py
  db.py
  ingestion/
    from_excel.py
    chunking.py
    upsert_chroma.py
  retrieval/
    embedder.py
    retriever.py
    expert_ranker.py
    store.py
  enquiry/
    classifier.py
    verifier.py
    processor.py
    approval.py
  llm/
    client.py
    grounding.py
    prompts.py
  utils/
data/
  processed_profiles/
tests/
requirements.txt
README.md
```

## Tech stack

- Python 3.11+
- FastAPI
- ChromaDB
- Pydantic
- OpenAI-compatible embeddings / LLM support
- OpenPyXL
- SQLite for local audit logging

## How it works

### 1. Data ingestion

Academic profile data is prepared from a structured source workbook and converted into JSON profile documents.

### 2. Chunking and indexing

Relevant profile fields such as biography, research interests, and publications are chunked and indexed in ChromaDB.

### 3. Enquiry processing

Incoming media enquiries are:

- verified against a simple ruleset
- classified into topic labels
- embedded and matched against indexed profile content

### 4. Expert recommendation

Retrieved chunks are aggregated at academic level and ranked using:

- retrieval score
- topic overlap
- simple fairness / repetition penalty
- evidence sufficiency filtering

### 5. Human approval

The system returns staff-facing recommendations, but any outreach remains manual and approval-gated.

## Local setup

### 1. Create and activate a virtual environment

**macOS / Linux**
```bash
python -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Create the environment file
```bash
cp .env.example .env
```

On Windows PowerShell:
```powershell
copy .env.example .env
```

Then add your API key to `.env` if you want live embeddings and optional LLM-generated staff summaries.

## Running the project

### Option A: index existing JSON profiles
```bash
python -m app.ingestion.upsert_chroma
uvicorn app.main:app --reload
```

### Option B: generate JSON profiles from the workbook first

Place the workbook in the project root as:
```
SOAS_profiles.xlsx
```

Then run:
```bash
python -m app.ingestion.from_excel
python -m app.ingestion.upsert_chroma
uvicorn app.main:app --reload
```

## API usage

Once running, open:
```
http://127.0.0.1:8000/docs
```

### Health check
```bash
curl http://127.0.0.1:8000/health
```

### Process a media enquiry
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

### Record an approval decision
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

## Example response shape

The enquiry processing endpoint returns:

- `enquiry_id`
- `created_at`
- `verification`
- `topic_labels`
- `recommended_experts`
- `requires_staff_approval`
- `staff_summary`

Each recommended expert includes:

- profile metadata
- supporting evidence chunks
- source URL
- score
- rationale
- matched topic signals

## Data handling and privacy

This repository excludes local secrets and generated local artefacts such as:

- `.env`
- local vector store
- generated processed profile JSON files
- local database files

The real source workbook and processed profile outputs are not included in the public repository.

This project is intended as an MVP for internal workflow support, not a production system and not a public-facing tool.

## Design principles

This MVP was built around a few core principles:

- **Grounded outputs only** — recommendations must be supported by retrieved profile evidence
- **Human oversight** — no automated outreach to academics
- **Proportionate verification** — recognised outlet emails can be fast-routed, while uncertain cases fall back to manual handling
- **Transparency** — each recommendation includes evidence and source links
- **Auditability** — enquiries and approvals are logged

## Known limitations

- classification is still simple and rule-based
- retrieval is currently vector-first rather than fully hybrid
- source text cleanliness depends on profile formatting quality
- fairness logic is still lightweight
- there is no dedicated frontend yet
- confidence scoring is not yet surfaced as an explicit field

## Suggested next improvements

- Replace rule-based classification with constrained LLM classification
- Add hybrid retrieval using BM25 plus vector search
- Improve metadata filtering by region, language, department, and media suitability
- Add confidence labels to recommendations
- Add fairness analytics to monitor repeated use of the same academics
- Add profile freshness checks and recrawling workflows
- Build a lightweight UI for press staff review and approval
- Add stronger evaluation metrics for relevance, diversity, and approval quality

## Intended use

This project was built as a practical, assessment-friendly MVP to demonstrate how a RAG system can support media-expert matching in a controlled institutional setting while remaining aligned with:

- human oversight
- GDPR-aware handling
- professional communications practice
- transparent and auditable decision support
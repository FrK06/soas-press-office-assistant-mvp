# SOAS Press Office Assistant MVP

A grounded, approval-gated Retrieval-Augmented Generation (RAG) prototype for matching media enquiries to relevant academic experts using SOAS-controlled profile data.

This repository is assessment-ready rather than production-ready. It is designed to demonstrate a transparent expert-matching workflow where press-office staff stay in control before any outreach happens.

## Overview

SOAS External Communications currently handles media enquiries through manual triage. This MVP supports that workflow by:

- capturing and processing incoming media enquiries
- applying proportionate sender verification rules
- retrieving relevant profile evidence from academic data
- recommending 3-5 suitable experts with source support
- generating a staff-facing summary
- requiring explicit staff approval before outreach
- logging operational decisions for audit and reporting

The system is intentionally staff-facing. It does not contact academics automatically and it does not generate ungrounded recommendations.

## Current architecture

```text
Enquiry intake
-> Sender verification
-> Topic classification
-> Semantic retrieval
-> Expert aggregation and ranking
-> Staff-facing summary
-> Approval decision logging
```

## Key features

- Grounded retrieval from structured academic profile content
- Approval-gated workflow before any outreach
- Configurable recognised-outlet verification rules
- Expert ranking using semantic retrieval plus topic-aware boosting
- Evidence-linked recommendations with supporting chunks and source URLs
- Optional LLM-generated staff summaries with deterministic fallback
- Audit logging for enquiries and approval decisions
- Excel-to-JSON ingestion pipeline for profile data preparation
- Local evaluation scripts and generated benchmark artefacts
- Lightweight staff-facing HTML UI plus JSON API

## Repository structure

```text
app/
  main.py
  config.py
  schemas.py
  db.py
  enquiry/
  evaluation/
  ingestion/
  llm/
  retrieval/
  static/
  templates/
  utils/
data/
  evaluation/
  processed_profiles/
tests/
README.md
requirements.txt
```

## Tech stack

- Python 3.11+
- FastAPI
- Pydantic / pydantic-settings
- ChromaDB
- OpenAI-compatible embeddings and optional LLM summaries
- OpenPyXL
- SQLite
- Pytest

## Setup

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

### 4. Configure credentials

- `OPENAI_API_KEY` is required for live embedding calls.
- Live indexing and live enquiry processing both require embeddings access.
- LLM-generated staff summaries are optional and remain disabled by default through `ENABLE_LLM_RATIONALES=false`.

## Running the project

### Use the committed processed-profile fixtures

```bash
python -m app.ingestion.upsert_chroma
uvicorn app.main:app --reload
```

The app initialises the SQLite schema automatically on startup.

### Regenerate processed-profile fixtures from the workbook

Place the workbook in the project root as:

```text
SOAS_profiles.xlsx
```

Then run:

```bash
python -m app.ingestion.from_excel
python -m app.ingestion.upsert_chroma
uvicorn app.main:app --reload
```

## API usage

Once the app is running, open:

```text
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

## Evaluation

The repository includes:

- gold datasets in `data/evaluation/`
- an evaluation runner at `app/evaluation/run_eval.py`
- plotting utilities at `app/evaluation/plot_eval.py`
- generated JSON, CSV, and figure outputs in `data/evaluation/`

Run the test suite from the repo root with:

```bash
python -m pytest
```

Run the evaluation scripts with:

```bash
python -m app.evaluation.run_eval
python -m app.evaluation.plot_eval
```

### Focused academic evaluation

The focused academic evaluation covers only `E1`, `E2`, `E4`, and `E5`.

- It uses the current fixed processed corpus across all runs.
- The supplied workbook at `C:\Users\Dario\Downloads\SOAS_PressOffice_PoC_AcademicProfiles.xlsx` is not used to regenerate the corpus in this pass.
- Groundedness requires manual annotation before scoring.

Run the focused evaluation scripts with:

```bash
python -m app.evaluation.run_focused_eval
python -m app.evaluation.export_groundedness_audit
python -m app.evaluation.score_groundedness
```

Evaluation runs are isolated from the operational audit log and do not write enquiry records into the runtime SQLite database.

## Data handling and artefact policy

This repository keeps a clear split between committed assessment fixtures and local runtime artefacts.

Committed fixtures:

- processed profile JSON files in `data/processed_profiles/`
- evaluation datasets and generated evaluation outputs in `data/evaluation/`

Local-only artefacts:

- `.env`
- `SOAS_profiles.xlsx`
- `chroma_store/`
- `press_office.db` and any other local SQLite files

## Design principles

- Grounded outputs only: recommendations must be supported by retrieved profile evidence
- Human oversight: no automated outreach to academics
- Proportionate verification: recognised outlet emails can be fast-routed, while uncertain cases fall back to manual handling
- Transparency: each recommendation includes evidence and source links
- Auditability: enquiries and approvals are logged

## Known limitations

- classification is still rule-based
- retrieval is currently vector-first rather than hybrid
- fairness logic is lightweight
- confidence labels are heuristic rather than calibrated
- the frontend is intentionally minimal
- this is not a production deployment or production governance model

## Intended use

This MVP demonstrates how a RAG system can support media-expert matching in a controlled institutional setting while remaining aligned with:

- human oversight
- transparent evidence use
- GDPR-aware handling
- professional communications practice
- auditable decision support


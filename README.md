# Agentic AI Recruitment

A recruitment platform that uses five specialized AI agents to extract CV information, verify documents, match candidates to job requirements, and generate an explainable report. Final recruitment decisions remain with a human recruiter.

## Current milestone

- [x] Initial repository structure
- [x] Development seed script (admin, candidate, published test offer)
- [ ] Authentication and role-based authorization
- [ ] Job offer CRUD
- [ ] Candidate application workflow
- [ ] Five AI agents and orchestrator

## Setup

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

Create a PostgreSQL database named `recruitment_db`, copy `.env.example` to `.env`, update credentials, then run:

```bash
python -m scripts.seed
```

The seed script creates development data only. Replace the example passwords and never commit `.env` or real candidate documents.

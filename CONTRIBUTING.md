# Contributing to Memory Board

Thank you for contributing to Memory Board!

## Development Setup

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- SQLite 3

### 2. Backend Setup
```bash
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
pip install -r api/requirements.txt
python -m api.app.ingest.pipeline
python -m uvicorn api.app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd web
npm install
npm run dev
```

### 4. Running Tests
```bash
# Backend pytest suite
pytest api/tests -v

# Evaluation simulator
python eval/simulate.py
```

## Pull Request Guidelines
- Ensure all automated tests pass before opening a PR.
- Write descriptive commit messages following the Conventional Commits specification (`feat:`, `fix:`, `docs:`, `test:`).

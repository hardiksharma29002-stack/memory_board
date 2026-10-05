# Memory Board — Build & Task Runner

.PHONY: setup dev api web ingest test eval wipe help

help:
	@echo "Available commands:"
	@echo "  make setup   - Install python requirements and dependencies"
	@echo "  make ingest  - Run photo ingestion on data/photos"
	@echo "  make api     - Start FastAPI backend (port 8000)"
	@echo "  make web     - Start web frontend (port 3000)"
	@echo "  make dev     - Start development servers"
	@echo "  make test    - Run test suite"
	@echo "  make wipe    - Wipe generated database, thumbs, and embeddings"

setup:
	python -m pip install -r api/requirements.txt

test:
	python -m pytest api/tests -v

eval:
	python eval/simulate.py

api:
	python -m uvicorn api.app.main:app --reload --host 0.0.0.0 --port 8000

web:
	cmd.exe /c "cd web && npm run dev"

ingest:
	python -m api.app.ingest.pipeline

sync:
	python -c "from api.app.ingest.pipeline import sync_unindexed_photos; sync_unindexed_photos(verbose=True)"

bench:
	python scripts/benchmark_latency.py

wipe:
	rm -rf data/thumbs/* data/app.db data/embeddings.npy


# Memory Board Architecture

## Overview
Memory Board is a cognitive photo retrieval system designed to locate photos based on human episodic memory rather than traditional keyword searches or manual chronological timeline scrolling.

```
                    ┌─────────────────────────┐
                    │   User Episodic Memory  │
                    │ (Time, Vibe, People...) │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │  Cognitive Cue Board    │
                    │   (4 Square Cards)      │
                    └───────────┬─────────────┘
                                │
         ┌──────────────────────┴──────────────────────┐
         ▼                                             ▼
┌─────────────────────────┐               ┌─────────────────────────┐
│   4 Candidate Albums    │               │  Guided Recall Sheet    │
│  (Calibrated Scores)    │               │(Entropy-Ranked Question)│
└───────────┬─────────────┘               └───────────┬─────────────┘
            │                                         │
            ▼                                         ▼
┌─────────────────────────┐               ┌─────────────────────────┐
│   Almost! Pivot Engine  │               │   Zero-Loss Fallback    │
│  (Near-Miss Adjustment) │               │   (3-Tier Recovery)     │
└─────────────────────────┘               └─────────────────────────┘
```

## Core Modules

### 1. Ingestion Pipeline (`api/app/ingest/`)
- **Metadata Extraction**: EXIF timestamp, width, height, camera model.
- **Rule-based & ML Tagging**: Face detection counts, dominant 3-color palette extraction, ambient brightness & sharpness metrics.
- **Self-Healing Indexing**: Automated recursive discovery of external photos and idempotent SQLite indexing.

### 2. Cognitive Retrieval Engine (`api/app/engine/`)
- **Cue Vocabulary (`vocab.py`)**: Multi-dimensional cues covering lighting, people, scene type, and time.
- **Dynamic Grouping (`groups.py`)**: K-Means feature clustering combined with memory cues to generate 4 uncluttered candidate albums.
- **Calibrated Confidence (`confidence.py`)**: Platt scaling / Isotonic regression yielding calibrated probabilities and qualitative bands (`Highest`, `Good`, `Possible`, `Unsure`).
- **Information-Gain Question Selection (`questions.py`)**: Shannon entropy ranking to choose the most informative next question among candidate photos.

### 3. Progressive Web Client (`web/`)
- **Next.js 14 App Router**: Clean UI with Tailwind CSS and Google Photos aesthetics.
- **Two-Stage Scroll Nudge**: Monitors scroll velocity and direction changes to detect aimless hunting, transitioning from gentle memory prompts to active scroll detection badges.
- **Question Sheet**: 4 large touch options with a dedicated "Can't recall" fallback.

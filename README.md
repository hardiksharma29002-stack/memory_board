# 🧠 Memory Board — Photo Retrieval Prototype

> Finding photos the way humans remember them: by cues, context, colors, and moments — not filenames or exact dates.

---

## 🌟 Key Features

1. **Incomplete Memory Search (1, 2, or 3 Clues)**:
   - Type freeform vague memories (e.g. *"night street food with friends near yellow lights"*).
   - Fast Groq LLM inference (`qwen/qwen3.8-27b`) and local rules automatically parse memories into structured cognitive anchors.
   - Quick 1-tap starter clue chips (*Festivals & Warm Lights*, *Street Food*, *Group of 3-5*, *Sunset Trip*, *Monuments*).

2. **Non-Pictorial Cognitive Cue Cards**:
   - Conceptual episodic triggers instead of thumbnail preview strips: Lighting & Atmosphere, Social Presence, Setting & Venue, Dominant Mood.
   - User can **type or select an option** at every point.

3. **4 Macro Albums with Calibrated Confidence Percentages**:
   - Clusters candidate photos into 4 macro albums of 15–20 photos each.
   - Every album features a bold, high-contrast confidence percentage pill (e.g. `88% High Confidence`, `74% Good Match`).

4. **Zero Context Loss Fallback & AI Probes**:
   - When tapping *"Not here"*, the system locks and preserves all active clues.
   - Synthesizes fresh contextual memory probes and checks simulated hiding places (Archive, Trash, Locked Folder, Device Storage).

5. **400+ Photo Dataset**:
   - 412 authentic Indian daily-life moments (festivals, street food, monuments, nature, night lights, family gatherings).
   - Local CLIP ViT-B/32 embeddings, k-means color palettes, and WebP thumbnails.

6. **Accessibility First ("Visible Even to a Blind")**:
   - WCAG AAA contrast compliance, bold indicators, min 48px touch targets.
   - Comprehensive ARIA screen reader attributes (`role="region"`, `role="checkbox"`, `aria-live="polite"`).

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.11+
- Node.js 18+

### 2. Setup Dependencies
```bash
pip install -r api/requirements.txt
cd web && npm install && cd ..
```

### 3. Run Ingestion Pipeline (400+ Photos)
```bash
python -m api.app.ingest.pipeline
```

### 4. Run Test Suite
```bash
python -m pytest api/tests -v
```

### 5. Start Development Servers
**Backend API (FastAPI on port 8000):**
```bash
python -m uvicorn api.app.main:app --port 8000
```
- Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/api/health](http://localhost:8000/api/health)

**Frontend Web App (Next.js on port 3000):**
```bash
cd web
npm run dev
```
- Open [http://localhost:3000](http://localhost:3000) in your browser!

### 6. Run Gate Simulation
```bash
python eval/simulate.py 150
```

---

## 📊 Evaluation & Metrics

| Metric | Target | Result | Status |
|---|---|---|---|
| **Found-in-3** | $\ge 60.0\%$ | **72.0%** | **Passed** ✅ |
| **Mean Steps to Found** | $\le 3.5$ | **2.7** | **Passed** ✅ |
| **Calibrated ECE** | $\le 0.10$ | **0.0000** | **Passed** ✅ |
| **Mean Items Scanned** | $\le 85.0$ | **68.8** | **Beats Timeline Scroll (206) & Keyword Search (85)** 🏆 |
| **Photo Library** | $\ge 400$ | **412 photos** | **Passed** ✅ |

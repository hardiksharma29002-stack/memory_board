# Memory Board — GTM, Risk & Mitigation Slide Content (Nykaa Layout)

---

## 1. TOP TITLE BANNER
**Managing Risk While Rolling Out Memory Board**

---

## 2. LEFT SECTION: FAILURE MODES + MITIGATION

### 🎯 The confidence score misleads or clusters unrelated photos
- **Risk:** Vague clue extraction groups irrelevant photos or displays abstract confidence percentages (e.g. "84% match") that contradict the user's mental model, eroding trust in AI retrieval.
- **Mitigation:** Abstract % scores are replaced with visible, explainable semantic clue chips (*"Golden Hour"*, *"Food / Cafe"*). Strict rank-clamping and tie-margin enforcement prevent misleading groupings. The false-positive guardrail (<10% dwell <2s) catches any erratic clustering immediately.

---

### ⚙️ The nudge interrupts or adds friction to regular browsing
- **Risk:** The *"Try Memory Search"* nudge triggers prematurely during casual timeline scrolling, irritating users and cannibalizing passive browsing engagement.
- **Mitigation:** Trigger shifts from simple scroll depth to a context-aware "lost browsing" signal (rapid bi-directional scrolling + dwell pause). The nudge is subtle, non-blocking, and 1-tap dismissible; timeline browsing stays completely untouched. Guardrail: Zero drop in DAU gallery browsing minutes.

---

### 👤 Guided narrowing feels like an interrogation / quiz
- **Risk:** Users with hazy memories experience cognitive fatigue when prompted for multiple successive details, triggering rapid drop-offs, guessing, or feeling they "failed to search."
- **Mitigation:** Strict hard cap of 2 questions maximum, backed by an instant *"Show Closest Photos Now"* early escape button. Every question includes a penalty-free *"Can't Recall"* option that advances smoothly. Question CTR and abandonment rates are tracked as immediate friction signals.

---

### ⚠️ The AI latency spikes or model call fails
- **Risk:** A slow or failing LLM call (Groq/Gemini) hangs the search (>3s latency) or crashes, leaving users staring at an endless spinner or an empty dead-end screen.
- **Mitigation:** A strict 4.5s timeout with in-memory LRU caching, paired with a deterministic regex heuristic fallback ladder that extracts cues and clusters photos offline in <100ms. p95 latency is held under 2.5s; the system guarantees zero broken states and zero *"No results found"* screens.

---

## 3. RIGHT TOP SECTION: GTM STRATEGY

### 🚀 Phase 1 — Soft Launch & Validate (Weeks 1–6)
- **Rollout:** Release Memory Board to a 5% cohort of high-volume smartphone photographers (>2,000 photos) exhibiting high scroll-hunting behavior. A/B test against the standard keyword search bar and timeline baseline.
- **Goal:** Confirm it lifts Vague Retrieval Success Rate (VRSR) to 35%+ without hurting regular gallery browsing minutes or increasing search abandonment.

---

### 📈 Phase 2 — Limited Rollout & Learning (Weeks 6–14)
- **Rollout:** Expand to 25% of active Google Photos mobile users (Android & iOS). Refine clue extraction prompts, canonical alias mappings, and clustering weights based on real usage telemetry, thumbs feedback, and voice clue inputs.
- **Goal:** Raise album tap-through rate (≥60%) and question completion (≥50%) while holding p95 latency strictly under 2.5s and false positives below 10%.

---

### 🌐 Phase 3 — Full Rollout & Ecosystem Integration (Weeks 14+)
- **Rollout:** Roll out 100% globally across Android, iOS, and Web. Integrate on-device multimodal embeddings (Gemini Nano) for instant, private, offline retrieval and seamless album resurfacing.
- **Goal:** Establish Memory Board as the default photo retrieval paradigm globally, driving VRSR to 45–50%+ and strengthening Google One storage subscription retention.

---

## 4. RIGHT BOTTOM SECTION: WHAT WINNING LOOKS LIKE AT 3 MONTHS

### 👤 For Users
- **Effortless Discovery:** Their camera roll is finally findable, decidable, and stress-free — no more endless scroll-hunting or guessing exact dates.
- **Rapid Recognition:** Vague memories (*"that night food stall with warm lights"*) convert into visual recognition and target photo retrieval in under 45 seconds.
- **Zero Dead-Ends:** Fuzzy recall leads to cognitive relief through vibe-based macro albums, never an empty *"No results found"* wall.

### 📷 For Google Photos
- **Step-Function Retrieval Lift:** Vague Retrieval Success Rate (VRSR) jumps from ~12% (keyword baseline) to 45–50%+ on ambiguous queries, turning dead searches into successful retrievals.
- **Higher Downstream Engagement:** Photo rediscovery directly drives downstream shares, favorites, and album creation without cannibalizing passive gallery exploration.
- **Platform Stickiness:** Transforms Google Photos from a passive cloud storage locker into an indispensable, intelligent memory companion, defending Google One retention and NPS.

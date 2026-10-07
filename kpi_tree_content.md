# KPI Tree — Increasing Vague Photo Retrieval (Memory Board)

---

## 1. TITLE
KPI Tree — Increasing Vague Photo Retrieval

---

## 2. NORTH STAR METRIC (Left Top Card)
NORTH STAR METRIC
% of active photo searchers successfully finding target photo / session (VRSR)
*Vague Retrieval Success Rate

---

## 3. NORTH STAR FORMULA (Left Bottom Card)
NORTH STAR FORMULA
VRSR = Narrowing Engagement Rate × Retrieval Resolution Rate

• Narrowing Engagement Rate: share of sessions where user actively engages with clue albums or guided questions.
• Retrieval Resolution Rate: how many narrowed sessions actually result in finding and viewing the target photo.
• False-Positive Rate (guardrail): must remain <10% — proof of genuine photo recognition, not guessing.

---

## 4. BRANCH 1: COGNITIVE NARROWING (Center Top Card)
Cognitive Narrowing
Users who engage with the narrowing loop
• Nudge Engagement Rate — taps on Try Memory Search
• Album Tap-Through Rate — taps on Jump to Album
• Guided Question CTR — answers question vs skip

---

## 5. BRANCH 2: RETRIEVAL & ACTION (Center Bottom Card)
Retrieval & Action
Narrowed sessions that locate target photo
• Photo Identification Rate — finds target photo (≥5s view)
• Post-Retrieval Action Rate — share / favorite / zoom
• False-Positive Rate — guardrail, not growth

---

## 6. METRICS TO MEASURE SUCCESS (Right Card — Exact Formulas)

METRICS TO MEASURE SUCCESS

Nudge Engagement Rate: How many scrolling gallery views result in a Memory Search tap.
metric: Taps on "Try Memory Search" ÷ Nudge impressions shown

Album Tap-Through Rate: How often confidence-ranked macro albums lead directly to an album dive.
metric: "Jump to Album" taps ÷ Macro album impressions

Guided Question CTR: How many narrowing questions get an actual answer instead of being skipped.
metric: Answered questions ÷ Questions shown

Photo Identification Rate: How often surfaced candidate photos contain the user's target memory.
metric: Target photos opened (≥5s view) ÷ Sessions reaching candidates

Post-Retrieval Action Rate: Whether finding the photo leads to active utility (share, favorite, zoom).
metric: Photos shared / favorited ÷ Target photos opened

False-Positive Rate: Guardrail — ensures users aren't rage-tapping random photos in frustration.
metric: Photo taps <2s dwell ÷ Total photo taps

VRSR Uplift: Direct movement on the North Star, before vs. after launch.
metric: (Post - Pre) ÷ Pre

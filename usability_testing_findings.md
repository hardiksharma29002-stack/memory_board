# Usability Testing (UT) — Memory Board Findings & V2 Iteration

---

## Slide Header Banner
> **Users Loved the Cognitive Relief, but Stumbled When Prompted for Too Many Details**

---

## Section 1: The Setup (1-Line Context)
- **Protocol**: 5 moderated 1:1 testing sessions with active smartphone photographers.
- **Scenario**: Given a vague recall task without exact dates (*"Find that night street food photo from a trip 2 years ago"*).
- **Task Success**: 4/5 participants (80%) successfully retrieved their target photo in under 75 seconds (vs. >4 min baseline gallery scrolling).

---

## Section 2: What Users Told Us (Attitudinal Feedback — 3 Lines)
1. *"I loved that I didn't have to remember dates or specific keywords — just typing what it felt like worked."*
2. *"The questions felt like a friend helping me jog my memory instead of a cold search bar."*
3. *"Seeing macro-albums grouped by vibe and lighting made me realize I was looking in the completely wrong year."*

---

## Section 3: What We Observed (Behavioral Reality — 3 Lines)
1. **Nudge Dismissal Friction**: 2 out of 5 users initially swiped away the scroll nudge because it appeared too quickly, mistaking it for an in-app promo before realizing it was search help.
2. **Confidence Score Confusion**: Users hesitated at abstract percentages (e.g., *"Confidence: 84%"*); they trusted visible clue chips (e.g., *"Matches: Sunset + Stadium"*) much more than mathematical scores.
3. **Question Fatigue Past Step 2**: If users encountered a 3rd guided question card, completion dropped sharply — users rapidly hit *"Can't recall"* just to force the gallery to open.

---

## Section 4: What We Are Doing in Next Iteration (Actionable V2 Fixes — 4 Lines)
1. **Context-Aware Nudge Trigger**: Shift nudge trigger from simple scroll depth to a "lost browsing" signal (rapid up-and-down scrolling + pause), cutting false dismissals.
2. **Semantic Match Badges over % Scores**: Replace abstract confidence percentages with visible matched-attribute chips (*"Outdoor Gathering"*, *"Golden Light"*) to build explainable AI trust.
3. **Hard Cap at 2 Questions + Early Escape**: Strictly cap guided questions at 2 rounds and add a prominent *"Show Closest Photos Now"* button so users never feel interrogated.
4. **Voice Clue Dictation**: Add a 1-tap mic input on the memory sheet, as 3/5 users expressed that speaking fuzzy memories feels far more natural than typing them out.

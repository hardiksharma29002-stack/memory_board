# Product Design Specification — Memory Board

> **Product:** Memory Board  
> **Prototype:** Photo retrieval through recognition instead of perfect keyword recall  
> **Design target:** Mobile-first, 390 × 844 px  
> **Primary surface:** Standalone prototype simulating Google Photos retrieval  
> **Design principle:** Don't make people describe a photo. Help them recognise it.

---

# 1. Design North Star

Memory Board should feel like a **visual conversation with the user's memory**, not like another search form.

The core problem is that people remember a photo as a story:

- who was there
- where they were
- what the light looked like
- what was happening
- what the photo felt like

But conventional search asks them to compress that memory into keywords.

The interface therefore needs to move through this loop:

**Remember → Recognise → Confirm → Narrow → Recognise again → Find**

The product should never make the user feel that they "failed to search."

If the first attempt is wrong, the UI should respond with:

> **"That's okay. Let's use another part of what you remember."**

rather than:

> **"No results found."**

---

# 2. Overall Visual Direction

## 2.1 Design language

Use a deliberate mix of:

1. **Google Photos familiarity**
   - clean
   - calm
   - image-first
   - trustworthy
   - minimal chrome

2. **Editorial / premium visual storytelling**
   - large imagery
   - generous whitespace
   - strong visual hierarchy
   - subtle typography
   - carefully controlled colour

3. **Modern AI product patterns**
   - soft surfaces
   - contextual chips
   - progressive disclosure
   - confidence states
   - conversational microcopy

4. **Memory / scrapbook cues**
   - visual fragments
   - small colour swatches
   - photo clusters
   - "ring a bell?" language
   - recognition over typing

Do **not** make it look like a generic AI chatbot.

Do **not** make it look like a dashboard.

Do **not** make every component rounded and colourful just because it is an AI prototype.

The visual language should communicate:

> **"I already know enough about what you remember to help you."**

---

# 3. Colour System

## 3.1 Core palette

Use a warm neutral base with Google-like blue as the primary interaction colour.

### Light theme

| Token | Value | Usage |
|---|---|---|
| `bg.canvas` | `#FAF9F7` | Main background |
| `bg.surface` | `#FFFFFF` | Cards / sheets |
| `bg.surfaceMuted` | `#F3F2F0` | Secondary surfaces |
| `text.primary` | `#202124` | Main text |
| `text.secondary` | `#5F6368` | Supporting text |
| `text.tertiary` | `#80868B` | Metadata |
| `border.subtle` | `#E6E3DE` | Dividers / borders |
| `primary` | `#1A73E8` | Primary actions |
| `primarySoft` | `#E8F0FE` | Selected state |
| `success` | `#188038` | Found / positive state |
| `successSoft` | `#E6F4EA` | Success background |
| `warning` | `#B06000` | Possible / uncertainty |
| `warningSoft` | `#FEF3E7` | Uncertainty background |
| `danger` | `#C5221F` | Destructive actions only |

### Dark theme

| Token | Value | Usage |
|---|---|---|
| `bg.canvas` | `#121212` | Main background |
| `bg.surface` | `#1E1E1E` | Cards |
| `bg.surfaceElevated` | `#282828` | Sheets / elevated cards |
| `text.primary` | `#F1F3F4` | Main text |
| `text.secondary` | `#BDC1C6` | Supporting text |
| `text.tertiary` | `#9AA0A6` | Metadata |
| `border.subtle` | `#3C4043` | Borders |
| `primary` | `#8AB4F8` | Primary interaction |
| `primarySoft` | `#203A5F` | Selected state |
| `success` | `#81C995` | Success |
| `successSoft` | `#1F3A27` | Success surface |
| `warning` | `#F6AD55` | Uncertainty |
| `warningSoft` | `#3B2D1A` | Uncertainty surface |

## 3.2 Colour usage rule

Colour should communicate **state**, not decoration.

Use:

- blue → action / selected / active
- green → found / strong positive
- amber → uncertainty / possible
- neutral → normal content
- red → only destructive or exceptional states

Do not colour-code every cue card.

The photos themselves should remain visually dominant.

---

# 4. Typography

## 4.1 Typeface

Preferred:

**Google Sans / Product Sans where available**

Fallback:

**Inter → system-ui → sans-serif**

## 4.2 Type scale

| Element | Size | Weight | Line height |
|---|---:|---:|---:|
| Screen title | 28 px | 600 | 34 px |
| Hero prompt | 26 px | 600 | 32 px |
| Section title | 20 px | 600 | 26 px |
| Card title | 16 px | 600 | 22 px |
| Body | 15 px | 400 | 22 px |
| Button | 15 px | 600 | 20 px |
| Chip | 13 px | 500 | 18 px |
| Caption | 12 px | 400 | 16 px |

Avoid excessive bold text.

Use hierarchy through:

**size → weight → spacing → colour**

not through multiple font colours.

---

# 5. Spacing System

Use an 8 px base grid.

```text
4   = micro spacing
8   = small
12  = compact
16  = standard
24  = section
32  = large
40  = hero
48+ = major separation
```

Mobile horizontal page padding:

```text
16 px
```

For hero screens:

```text
20 px
```

Never allow content to touch the screen edge unless it is an intentional full-bleed photo.

---

# 6. Border Radius

Use a restrained radius system.

| Component | Radius |
|---|---:|
| Small chip | 999 px |
| Button | 999 px |
| Cue card | 20 px |
| Group card | 20 px |
| Question option | 16 px |
| Bottom sheet | 28 px top |
| Photo tile | 12 px |
| Image gallery | 12–16 px |

Avoid making every element look like a pill.

Pills are reserved for:

- chips
- filters
- compact actions
- confidence labels

---

# 7. Shadows and Elevation

Keep elevation subtle.

### Level 0

No shadow.

Used for:

- timeline
- flat content

### Level 1

```css
box-shadow: 0 2px 8px rgba(0,0,0,0.06);
```

Used for:

- cue cards
- group cards

### Level 2

```css
box-shadow: 0 8px 24px rgba(0,0,0,0.10);
```

Used for:

- bottom sheets
- important overlays

Avoid floating-card overload.

---

# 8. Image Treatment

Photos are the strongest visual element in the experience.

## Rules

- Never apply decorative filters.
- Preserve natural image colour.
- Use object-fit: cover for thumbnails.
- Use object-fit: contain for the final found image.
- Use consistent corner radius.
- Prefer visual diversity inside a group.
- Never show three nearly identical thumbnails when trying to help recognition.

## Cue card thumbnails

Each cue card contains:

```text
[large cue label]

[swatch] [swatch] [swatch]

┌─────┬─────┬─────┐
│ img │ img │ img │
└─────┴─────┴─────┘
```

The three images should deliberately vary.

Example:

**Warm yellow light**

- indoor dinner
- stage lighting
- street at night

This helps the user recognise the **visual concept**, not just one example image.

---

# 9. Global Navigation / Chrome

Keep navigation extremely light.

The prototype should feel like a focused extension of a photo gallery.

## Timeline header

```text
┌──────────────────────────────────────┐
│  Photos                         ⋮    │
│                                      │
│  [ 🔍 Search photos... ]             │
│                                      │
│  [ ✨ Find by memory ]               │
└──────────────────────────────────────┘
```

The **Find by memory** action should visually stand apart from normal keyword search.

It should not look like another text field.

---

# 10. Screen 1 — Timeline

## Purpose

This is the existing behaviour.

The user is already scrolling through photos.

The product should intervene only when there is evidence that the user is hunting.

## Layout

```text
Photos
────────────────────────

[ Search photos... ]

[ ✨ Find by memory ]

October 2026
┌────┬────┬────┐
│    │    │    │
├────┼────┼────┤
│    │    │    │
└────┴────┴────┘

September 2026
...
```

## Nudge

After the configured hunting behaviour:

```text
┌──────────────────────────────────────┐
│                                      │
│  Looking for a photo?                │
│                                      │
│  Find it by what you remember.       │
│                                      │
│  [ Find by memory ]                  │
│  [ Not now ]                         │
│                                      │
└──────────────────────────────────────┘
```

### Design principle

The nudge should feel like **help**, not an advertisement.

Do not use:

- bright gradients
- notification red
- animated bouncing
- intrusive modal takeover

Use a calm bottom sheet.

---

# 11. Screen 2 — Memory Board / Cue Board

This is the most important screen in the product.

## Primary job

Convert vague memory into visual recognition.

## Header

Use:

> **Does any of these ring a bell?**

Secondary line:

> Pick anything that feels familiar. You don't need to be sure.

The secondary line is optional if vertical space is tight.

## Layout

```text
← Memory search

Does any of these
ring a bell?

Pick anything that feels familiar.

┌─────────────────────────────┐
│ Warm yellow light           │
│                             │
│  ●  ●  ●                    │
│                             │
│ [img] [img] [img]           │
│                             │
│                     ○       │
└─────────────────────────────┘

┌─────────────────────────────┐
│ Outdoors                    │
│                             │
│  ●  ●  ●                    │
│                             │
│ [img] [img] [img]           │
└─────────────────────────────┘

┌─────────────────────────────┐
│ 3–5 people                  │
│ ...                         │
└─────────────────────────────┘

[ None of these ]    [ Not sure ]
```

## Card behaviour

Default:

- white surface
- subtle border
- no heavy shadow

Selected:

- blue 2 px border
- very light blue background
- selected checkmark
- subtle scale: 0.99

Do not animate cards dramatically.

## Important interaction

Multiple cards can be selected.

Example:

```text
✓ Warm yellow light
✓ 3–5 people
✓ Event venue
```

Then a single primary CTA appears:

> **Show me photos**

The user should not need to select exactly one clue.

---

# 12. Cue Card Design

Each card has four visual layers.

### Layer 1 — Label

Large enough to scan quickly.

Example:

**Warm yellow light**

### Layer 2 — Colour evidence

Three tiny swatches.

These are not decoration.

They answer:

> "What does this cue actually look like in my library?"

### Layer 3 — Recognition evidence

Three thumbnails.

### Layer 4 — Selection state

Clear checkmark / border.

## Example

```text
┌───────────────────────────────┐
│ Warm yellow light          ✓   │
│                               │
│  ●  ●  ●                      │
│                               │
│ ┌────┐ ┌────┐ ┌────┐          │
│ │    │ │    │ │    │          │
│ │    │ │    │ │    │          │
│ └────┘ └────┘ └────┘          │
└───────────────────────────────┘
```

---

# 13. Screen 3 — Groups / Visual Results

After the user confirms clues, show groups instead of one giant result list.

## Header

> **These look promising**

Supporting line:

> Based on what you remembered.

Then show the clue trail:

```text
Warm yellow light  ×   3–5 people ×
```

The trail is persistent and editable.

---

# 14. Group Card

A group is a visual hypothesis.

It should answer four questions immediately:

1. What kind of photos are these?
2. How likely are they?
3. Why did I get them?
4. What can I do next?

## Layout

```text
┌──────────────────────────────────┐
│ Highest chance                   │
│                                  │
│ Warm light · 3 people            │
│                                  │
│ Why this group                   │
│ [ yellow light ] [ 3 people ]    │
│                                  │
│ ┌──┬──┬──┬──┐                    │
│ │  │  │  │  │                    │
│ ├──┼──┼──┼──┤                    │
│ │  │  │  │  │                    │
│ └──┴──┴──┴──┘                    │
│                                  │
│ Confidence rose after your       │
│ last answer.                     │
│                                  │
│ [ Found it ] [ Almost! ]         │
│ [ Not here ]                     │
└──────────────────────────────────┘
```

---

# 15. Confidence Design

Do **not** initially show:

> 82% confidence

This creates false precision.

Instead show:

- Highest chance
- Good chance
- Possible
- Not sure yet

## Visual treatment

### Highest chance

Green-tinted badge.

### Good chance

Blue-tinted badge.

### Possible

Amber-tinted badge.

### Unsure

Neutral/amber text.

## "Why" explanation

Always expose the reason.

Example:

> **Why this group**
>
> Warm yellow light · 3 people

This is more important than the confidence label itself.

## Confidence movement

When confidence changes:

> **Confidence rose after your last answer**

or

> **This moved up because you chose "Evening."**

Keep this small.

It should explain movement without becoming a technical ML explanation.

---

# 16. Clue Trail

The clue trail is a core product element.

It makes the search feel cumulative.

```text
You remember:

[ Warm light × ] [ 3 people × ] [ Evening × ]
```

Every chip can be removed.

## Interaction

Tap ×:

1. remove clue
2. recompute groups
3. preserve the rest of the session

Add:

> **Rewind**

Rewind should undo the last decision.

The mental model is:

> "I can explore without losing what I already found."

---

# 17. Screen 4 — Guided Recall

When the user says:

> None of these

do not show an empty state.

Instead open a bottom sheet.

## Header

> **Let's try another part of the memory.**

Then:

> **What time of day was it?**

Four large options:

```text
┌─────────────────────┐
│ Morning             │
└─────────────────────┘

┌─────────────────────┐
│ Afternoon           │
└─────────────────────┘

┌─────────────────────┐
│ Evening             │
└─────────────────────┘

┌─────────────────────┐
│ Night               │
└─────────────────────┘

        Can't recall
```

## Design principle

"Can't recall" must be a normal option.

Never hide it in tiny text.

Never make it look like failure.

---

# 18. Question Selection UX

The engine decides which question is most useful.

The UI should not expose information gain, entropy, or scoring.

The user only sees a natural question.

Examples:

> What was in the background?

> How many people were in it?

> What colour stood out?

> How did it reach you?

## Progress

```text
1 of 3
```

Use a very subtle progress indicator.

Do not make it feel like a form.

---

# 19. Fill-the-Sentence Mode

This is an alternative recognition route.

Entry:

> **Fill it in**

Example:

> It was **[ evening ]**,  
> **[ outdoors ]**,  
> with **[ 3–5 people ]**,  
> near **[ greenery ]**.

Each blank opens the same four-option sheet.

## Visual treatment

Use an editorial sentence layout.

The selected values should look like interactive memory fragments:

```text
It was [ evening ],
     [ outdoors ],
with [ 3–5 people ],
near [ greenery ].
```

Selected blanks use the primary blue.

Empty blanks use a dotted underline.

---

# 20. Screen 5 — Almost!

"Almost!" is important because users often recognise the **kind of photo** without recognising the exact photo.

## Trigger

User taps:

> Almost!

on a result.

## Bottom sheet

Header:

> **What's different?**

Options:

```text
Different place
Different time of day
Different people
Different look
Can't say
```

## Tone

This should feel like refinement, not correction.

Avoid:

> "Why is this wrong?"

Prefer:

> "What's different?"

---

# 21. Screen 6 — Not Here / Fallback

Never show:

> No results.

Instead show the system continuing the search.

## Step 1 — Relax

Example:

> **Let's loosen one clue.**
>
> We removed "Evening" because it was the least certain clue.

Button:

> **Try again**

## Step 2 — Ask

If useful:

> **One more thing might help.**

Then show one question.

## Step 3 — Hiding places

If phase 7 is enabled:

```text
We also checked:

✓ Archive
✓ Trash
✓ Locked
✓ Not backed up
```

## Step 4 — Timeline

Final fallback:

> **We couldn't narrow it down further.**
>
> Your clues are still applied to the timeline.

Then show:

```text
[ Warm light × ] [ 3 people × ]

Timeline results
```

The user still has control.

---

# 22. Screen 7 — Found

When the user taps:

> Found it

stop the search immediately.

Do not ask another question.

Do not show another confidence screen.

## Layout

```text
← Back

             Found it

┌─────────────────────────────┐
│                             │
│                             │
│        BEST PHOTO            │
│                             │
│                             │
└─────────────────────────────┘

Other photos
[ ] [ ] [ ] [ ] [ ]

You found the photo.

[ Share ]
[ Post ]
[ Add to album ]
```

## Emotional moment

The found screen should feel noticeably calmer.

Reduce UI density.

Let the photo become the hero.

---

# 23. Best-Shot Selection

The best image in the group should be surfaced first.

Use:

```text
best =
0.6 × normalized sharpness
+
0.4 × exposure score
```

Do not expose this algorithm in the UI.

---

# 24. Bottom Sheets

Bottom sheets should be the main interaction pattern for:

- Guided Recall
- Almost
- Nudge
- optional source questions

## Sheet anatomy

```text
┌────────────────────────────────────┐
│                                    │
│             ─────                  │
│                                    │
│  Question                          │
│                                    │
│  Supporting explanation            │
│                                    │
│  [ option ]                        │
│  [ option ]                        │
│  [ option ]                        │
│  [ option ]                        │
│                                    │
│  Can't recall                      │
│                                    │
└────────────────────────────────────┘
```

Use a large top radius.

No heavy modal border.

---

# 25. Motion Design

Motion should explain state changes.

Do not use motion for decoration.

## Recommended transitions

### Cue selected

150 ms:

```text
border + background transition
```

### Results appearing

200–250 ms:

```text
opacity + translateY(8px → 0)
```

### Bottom sheet

250 ms:

```text
translateY(100% → 0)
```

### Confidence movement

Subtle 200 ms highlight around the changed badge.

### Found

No celebration animation.

The photo itself is the reward.

---

# 26. Loading States

Every screen must show a skeleton quickly.

Target:

**Skeleton ≤ 100 ms**

## Cue Board skeleton

```text
Does any of these
ring a bell?

┌──────────────────────┐
│ █████████             │
│                       │
│ ███ ███ ███           │
│                       │
│ ███████████████       │
└──────────────────────┘
```

Use low-contrast neutral shimmer.

Do not use animated rainbow gradients.

---

# 27. Empty / Error States

## Empty library

> **Your photo library is empty.**
>
> Add some photos to try Memory Board.

## Processing error

> **We couldn't prepare your photos yet.**
>
> Try again.

## Search error

> **Something went wrong while narrowing this down.**
>
> Your previous clues are still saved.

Button:

> **Try again**

Never say:

> Error 500

or expose technical terminology.

---

# 28. Accessibility

Must support:

- WCAG AA contrast
- minimum 48 × 48 px touch targets
- dynamic text size
- screen reader labels
- keyboard navigation
- visible focus state
- semantic buttons
- no colour-only state communication

Example:

Do not communicate:

> green = highest chance

only through colour.

Also show:

> Highest chance

as text.

---

# 29. Responsive Behaviour

Primary target:

```text
390 × 844
```

Also support:

```text
360 × 800
412 × 915
768 × 1024
```

## Mobile

Single-column flow.

## Tablet

Allow slightly wider cards but preserve:

- large imagery
- single decision per screen
- limited content density

Do not convert the prototype into a dashboard.

---

# 30. Component Architecture

Suggested component tree:

```text
App
├── Timeline
│   ├── SearchBar
│   ├── MemoryButton
│   ├── PhotoGrid
│   └── ScrollNudge
│
├── MemorySearch
│   ├── ClueTrail
│   ├── CueBoard
│   │   └── CueCard
│   ├── SentenceMode
│   ├── GroupResults
│   │   └── GroupCard
│   ├── QuestionSheet
│   ├── AlmostSheet
│   ├── FallbackView
│   └── FoundView
│
└── Shared
    ├── Button
    ├── Chip
    ├── Badge
    ├── PhotoTile
    ├── BottomSheet
    ├── Skeleton
    └── Toast
```

---

# 31. Component Rules

## Button

Variants:

```text
primary
secondary
text
danger
```

Primary should be used for the one most important action.

Avoid multiple primary buttons on one screen.

## Chip

Used for:

- clues
- why explanations
- filters

Not used for:

- long paragraphs
- major navigation

## Badge

Used for:

- confidence
- status

## PhotoTile

Must support:

- lazy loading
- selected state
- accessible label
- fixed aspect ratio
- fallback image

---

# 32. Interaction Hierarchy

Every screen should have:

### 1. One primary decision

Example:

> Pick the clues that feel familiar.

### 2. One primary action

Example:

> Show me photos

### 3. Secondary escape

Example:

> Not sure

### 4. Persistent context

Example:

> Clue trail

This prevents decision overload.

---

# 33. Design the Experience Around the Two Barriers

The problem has two core barriers.

## Barrier A — Starting

> "I remember the photo, but I don't know what to type."

Design response:

**Cue Board**

It gives the user visual starting points.

The user does not have to formulate a query.

---

## Barrier B — Continuing

> "My first search didn't work, and I don't know what to try next."

Design response:

**Guided Recall + Clue Trail + Almost + Fallback**

Every failed step creates the next possible action.

This is the central product behaviour.

---

# 34. Recognition Over Recall

Every important design decision should pass this test:

> **Can the user recognise the answer instead of having to remember the exact word?**

Good:

> Warm yellow light  
> [photos]

Good:

> What colour stood out?  
> [Warm yellow] [Cool blue] [Dark] [Bright white]

Good:

> What was different?  
> [Place] [Time] [People] [Look]

Bad:

> Enter keywords

Bad:

> Describe your photo

Bad:

> Tell us exactly what happened

---

# 35. Visual Hierarchy by Screen

## Timeline

```text
Search
↓
Find by memory
↓
Photos
```

## Cue Board

```text
Prompt
↓
Visual cards
↓
Primary action
```

## Groups

```text
Confidence
↓
Group explanation
↓
Photos
↓
Actions
```

## Question

```text
Question
↓
Options
↓
Can't recall
```

## Found

```text
Photo
↓
Confirmation
↓
Actions
```

---

# 36. Do Not Overdesign

Avoid:

- excessive gradients
- glassmorphism
- neon AI colours
- giant AI icons
- chatbot bubbles
- animated particles
- unnecessary illustrations
- excessive shadows
- huge headers
- dense analytics UI
- fake 3D cards

The prototype should look credible enough that someone could imagine it becoming part of a real photo product.

---

# 37. Suggested Visual Motif

Use a subtle **memory fragment** motif.

Not literal brain icons.

Instead use:

- photo fragments
- colour swatches
- stacked thumbnails
- small clue chips
- gentle transitions between fragments

The visual metaphor is:

**A memory is incomplete, but each fragment helps reconstruct it.**

---

# 38. Suggested Iconography

Use simple outlined icons.

Recommended:

- Search
- Sparkle / memory
- Check
- X
- Undo
- Arrow left
- Arrow right
- Share
- More
- Image
- Question
- Sliders

Avoid excessive icon labels.

Icons should support text, not replace it.

---

# 39. Microcopy Principles

Copy should be:

- short
- human
- reassuring
- direct
- non-technical

## Prefer

> Does any of these ring a bell?

> These look promising.

> What's different?

> One more thing might help.

> Not sure yet.

> Let's try another clue.

## Avoid

> Query refinement required.

> Search confidence score: 0.63.

> No relevant results were found.

> AI-generated semantic retrieval failed.

> Please provide additional information.

---

# 40. Design States Matrix

Every major component should support:

| State | Requirement |
|---|---|
| Default | Normal visual hierarchy |
| Hover | Desktop only |
| Focus | Accessible focus ring |
| Selected | Clear blue selection |
| Loading | Skeleton |
| Disabled | Reduced contrast |
| Error | Plain-language recovery |
| Empty | Helpful next action |
| Success | Clear confirmation |

---

# 41. Prototype Demo Path

For the final demo, make the happy path extremely polished.

Recommended flow:

```text
Timeline
   ↓
Find by memory
   ↓
Cue Board
   ↓
Warm yellow light + 3–5 people
   ↓
Groups
   ↓
Almost!
   ↓
Different time of day
   ↓
Groups improve
   ↓
Found it
   ↓
Hero photo
```

Also demonstrate the failure path:

```text
Cue Board
   ↓
None of these
   ↓
Question
   ↓
Can't recall
   ↓
Question
   ↓
Groups
   ↓
Not here
   ↓
Relax clue
   ↓
Timeline fallback
```

This proves the core thesis:

> **The search never dead-ends.**

---

# 42. Design QA Checklist

Before calling a screen complete:

## Visual

- [ ] Typography matches system
- [ ] Spacing follows 8 px grid
- [ ] Colours use tokens
- [ ] No unnecessary gradients
- [ ] Photos are sharp
- [ ] Cards do not look repetitive
- [ ] Primary action is obvious
- [ ] No visual clutter

## UX

- [ ] Only one major decision per screen
- [ ] User always knows what to do next
- [ ] Previous clues remain visible
- [ ] "Can't recall" is equally accessible
- [ ] No dead-end state
- [ ] Back / rewind behaviour is predictable

## Accessibility

- [ ] Touch targets ≥ 48 px
- [ ] WCAG AA contrast
- [ ] Screen-reader labels
- [ ] Focus states
- [ ] Dynamic text supported

## Performance

- [ ] Skeleton appears quickly
- [ ] Images lazy load
- [ ] No layout jumping
- [ ] Board ≤ 1 s end-to-end target
- [ ] API ≤ 300 ms p95 target

---

# 43. Implementation Guidance for an AI Coding Agent

Build the visual system **before** implementing every feature.

Recommended order:

### Step 1 — Design tokens

Create:

```text
colors
typography
spacing
radius
shadows
motion
breakpoints
```

in one central theme/configuration file.

Do not hard-code visual values throughout components.

### Step 2 — Build the primitives

Build:

```text
Button
Chip
Badge
PhotoTile
BottomSheet
Skeleton
```

### Step 3 — Build the Cue Card

Perfect this component first.

It is the visual signature of Memory Board.

### Step 4 — Build the Group Card

Make the confidence / why / photo hierarchy very clear.

### Step 5 — Build the Question Sheet

Keep it extremely simple.

### Step 6 — Connect the flow

```text
Timeline
→ Cue Board
→ Groups
→ Question
→ Groups
→ Found
```

### Step 7 — Add fallback behaviour

Implement:

```text
Almost
Not here
Relax
Rewind
Timeline fallback
```

### Step 8 — Add polish

Only after functionality works:

- transitions
- skeletons
- micro-interactions
- responsive adjustments
- accessibility
- empty/error states

---

# 44. Visual Acceptance Criteria

A reviewer should be able to look at the prototype and immediately understand:

### 1. This is about photos

The interface is image-led.

### 2. This is not normal search

The user chooses memories rather than typing keywords.

### 3. The system learns from every answer

The clue trail makes this visible.

### 4. The system does not pretend to know more than it does

Confidence uses bands rather than fake precision.

### 5. Failure is productive

There is always another path.

### 6. Recognition is the core interaction

The user repeatedly reacts to visual examples and simple choices.

---

# 45. Final Design Principle

The entire experience should communicate one idea:

> **You don't need to remember the words. You only need to recognise the clues.**

The user should enter the experience thinking:

> "I have no idea what to search."

and leave thinking:

> "I didn't have to search. I just recognised it."

That is the design difference Memory Board needs to make.

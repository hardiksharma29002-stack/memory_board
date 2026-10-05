# Scroll Hunting Detection Heuristics

## Cognitive Psychological Motivation
When searching for a lost memory, humans often resort to rapid manual scrolling through chronological feeds. However, recognition degrades sharply during rapid visual scanning due to cognitive fatigue and attentional blink.

Memory Board uses proactive behavioral nudging to detect when a user is hunting aimlessly and transition them to cognitive recall.

## Detection Pipeline

```
[User on Timeline]
       │
       ▼ (1 second idle)
[Initial Nudge: "Find photos by memory"]
       │
       ▼ (1.2s - 2.0s active continuous scrolling)
[Stage 2: "⚡ Scrolling detected"]
       │
       ▼ (Click "Find by memory")
[Launch Cognitive Cue Board]
```

## Heuristic Signals
1. **Initial Idle Prompt**: Reminds the user that memory cues are available.
2. **Scroll Continuity**: Detects continuous scroll gestures where timestamp delta < 1500ms.
3. **Directional Reversals**: Rapid directional shifts (scrolling down, then up, then down) signify hunting.
4. **Suppression Guards**:
   - Suppressed during quiet periods immediately after finding a photo.
   - Respects user dismissal per session.

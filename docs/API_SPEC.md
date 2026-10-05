# Memory Board REST API Specification

Base URL: `http://localhost:8000` (Direct) or `/api` (via Next.js Proxy)

## Endpoints

### 1. System Health
- **`GET /api/health`**
  - Response: `{ status: "ok", photos_indexed: int, thumbnails_cached: int, config_loaded: bool }`

### 2. Photos & Gallery
- **`GET /api/photos`**
  - Query params: `limit` (default 100), `offset` (default 0)
  - Returns paginated list of photo objects with thumbnail URIs and color palettes.
- **`GET /api/photos/{id}/thumb`**
  - Query param: `size` (`256` or `1024`)
  - Returns image binary (`image/jpeg` or `image/webp`).
- **`GET /api/photos/{id}/raw`**
  - Returns original photo binary.
- **`POST /api/photos/upload`**
  - Form-data: `files` (multi-file), `replace` (`true`/`false`)
  - Ingests external photos, generates thumbnails, and returns processed counts.
- **`DELETE /api/photos/{id}`**
  - Removes photo entry and cached thumbnails.

### 3. Cognitive Search Sessions
- **`POST /api/session`**
  - Body: `{ entry: string, initial_query?: string }`
  - Initializes session, parses vague memory into initial cues, and generates 4 cognitive cards.
- **`POST /api/session/{id}/cues`**
  - Body: `{ cue_ids: string[] }`
  - Applies selected cues, refines candidates, and returns 4 macro albums.
- **`POST /api/session/{id}/none`**
  - Transitions session to question flow, selecting the maximum information-gain question.
- **`POST /api/session/{id}/answer`**
  - Body: `{ question_id: string, option_id: string }`
  - Handles option selection or `"cant_recall"` and returns either the next question or refined albums.
- **`POST /api/session/{id}/almost`**
  - Body: `{ photo_id: string, axis: string }`
  - Performs dimensional pivot away from near-miss attributes.
- **`POST /api/session/{id}/fallback`**
  - Executes 3-tier zero-loss recovery ladder.

### 4. Telemetry Events
- **`POST /api/events`**
  - Body: `{ events: Array<{ name, session_id, ts, payload }> }`
  - Stores local telemetry events in SQLite.

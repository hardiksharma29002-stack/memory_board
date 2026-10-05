import {
  PhotoItem,
  SearchSessionState,
  CueCardItem,
  GroupCardItem,
  QuestionItem,
  ClueItem,
} from './types';

const API_BASE = ''; // Uses Next.js proxy rewrites

export async function fetchPhotos(limit = 100, offset = 0): Promise<{ photos: PhotoItem[]; total: number }> {
  const res = await fetch(`${API_BASE}/api/photos?limit=${limit}&offset=${offset}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch photos');
  return res.json();
}

export async function startSearchSession(entry = 'search_pill', initial_query?: string): Promise<{
  session_id: string;
  step: 'cue_board';
  cards: CueCardItem[];
  cognitive_cards?: import('./types').CognitiveCardItem[];
  initial_clues?: ClueItem[];
}> {
  const res = await fetch(`${API_BASE}/api/session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ entry, initial_query }),
  });
  if (!res.ok) throw new Error('Failed to start session');
  return res.json();
}

export async function fetchSession(sessionId: string): Promise<SearchSessionState> {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch session');
  return res.json();
}

export async function selectCues(
  sessionId: string,
  cueIds: string[]
): Promise<{ session_id: string; step: string; clues: ClueItem[]; groups: GroupCardItem[] }> {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}/cues`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ cue_ids: cueIds }),
  });
  if (!res.ok) throw new Error('Failed to select cues');
  return res.json();
}

export async function noneOfThese(
  sessionId: string
): Promise<{ session_id: string; step: 'question'; question: QuestionItem }> {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}/none`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to transition to question');
  return res.json();
}

export async function answerQuestion(
  sessionId: string,
  questionId: string,
  optionId: string
): Promise<{ session_id: string; step: string; clues: ClueItem[]; question?: QuestionItem; groups?: GroupCardItem[] }> {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}/answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question_id: questionId, option_id: optionId }),
  });
  if (!res.ok) throw new Error('Failed to answer question');
  return res.json();
}

export async function removeClue(
  sessionId: string,
  clueId: string
): Promise<{ session_id: string; step: string; clues: ClueItem[] }> {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}/clue/remove`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ clue_id: clueId }),
  });
  if (!res.ok) throw new Error('Failed to remove clue');
  return res.json();
}

export async function rewindSession(
  sessionId: string
): Promise<{ session_id: string; step: string; clues: ClueItem[] }> {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}/rewind`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to rewind session');
  return res.json();
}

export async function almostPivot(
  sessionId: string,
  photoId: string,
  differenceAxis: string
): Promise<{ session_id: string; step: 'almost'; photos: PhotoItem[] }> {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}/almost`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ photo_id: photoId, difference_axis: differenceAxis }),
  });
  if (!res.ok) throw new Error('Failed to pivot search');
  return res.json();
}

export async function confirmFound(
  sessionId: string,
  photoId: string
): Promise<{ session_id: string; status: string; outcome: string; found_photo_id: string }> {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}/found`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ photo_id: photoId }),
  });
  if (!res.ok) throw new Error('Failed to confirm found');
  return res.json();
}

export async function submitSentence(
  sessionId: string,
  blanks: Record<string, string>
): Promise<{ session_id: string; step: string; clues: ClueItem[]; groups: GroupCardItem[] }> {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}/sentence`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ blanks }),
  });
  if (!res.ok) throw new Error('Failed to submit sentence');
  return res.json();
}

export async function triggerFallback(
  sessionId: string
): Promise<{
  session_id: string;
  step: 'fallback';
  level: number;
  message: string;
  relaxed_clue_ids: string[];
  suggested_question_id?: string;
  timeline_jump_date?: string;
  clues?: ClueItem[];
  followup_probes?: import('./types').FollowupProbeItem[];
  preserved_context?: string[];
  cognitive_cards?: import('./types').CognitiveCardItem[];
}> {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}/fallback`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to trigger fallback');
  return res.json();
}

export async function addMemoryText(
  sessionId: string,
  text: string
): Promise<{ session_id: string; step: string; clues: ClueItem[]; groups: GroupCardItem[] }> {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}/add-memory-text`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error('Failed to add memory text');
  return res.json();
}

export async function parseMemory(
  query: string
): Promise<{ query: string; clues: Array<{ cue_id: string; label: string; source: string }> }> {
  const res = await fetch(`${API_BASE}/api/session/parse-memory`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error('Failed to parse memory');
  return res.json();
}

export async function fetchPhotoStats(): Promise<{
  total_photos: number;
  cap: number;
  available_slots: number;
  nudge_message: string;
  has_sample_backup: boolean;
}> {
  const res = await fetch(`${API_BASE}/api/photos/stats`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch photo stats');
  return res.json();
}

export async function uploadPhotos(
  files: File[],
  replace = false
): Promise<{
  status: string;
  uploaded_count: number;
  indexed_count: number;
  total_photos: number;
  cap: number;
  message: string;
}> {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  formData.append('replace', String(replace));

  const res = await fetch(`${API_BASE}/api/photos/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to upload photos');
  }
  return res.json();
}

export async function resetSamplePhotos(): Promise<{
  status: string;
  total_photos: number;
  message: string;
}> {
  const res = await fetch(`${API_BASE}/api/photos/reset-sample`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to reset sample photos');
  return res.json();
}

export async function fetchSmartCards(
  query?: string,
  selectedClues?: string[]
): Promise<{ cards: import('./types').CognitiveCardItem[] }> {
  const res = await fetch(`${API_BASE}/api/session/smart-cards`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, selected_clues: selectedClues }),
  });
  if (!res.ok) throw new Error('Failed to generate smart cards');
  return res.json();
}

export async function deletePhoto(photoId: string): Promise<{ status: string; deleted_id: string; message: string }> {
  const res = await fetch(`${API_BASE}/api/photos/${photoId}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete photo');
  return res.json();
}

export async function skipToAlbums(
  sessionId: string
): Promise<{ session_id: string; step: string; clues: ClueItem[]; groups: GroupCardItem[] }> {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}/skip-to-albums`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to skip to albums');
  return res.json();
}





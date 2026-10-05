export interface PhotoItem {
  id: string;
  path: string;
  taken_at?: string;
  hour_bucket?: number;
  width?: number;
  height?: number;
  palette?: string; // JSON string of 3 hex colors
  source?: string;
  thumb_256: string;
  thumb_1024: string;
}

export interface ClueItem {
  id: string;
  type: 'cue' | 'answer' | 'source' | 'almost' | 'text';
  label: string;
  value: string;
  cue_id?: string;
  weight: number;
  step_index: number;
}

export interface CueCardItem {
  cue_id: string;
  label: string;
  group: string;
  photo_count: number;
  preview_photo_ids: string[];
  palette: string[];
}

export interface GroupConfidence {
  raw: number;
  calibrated: number;
  percentage?: number;
  percentage_label?: string;
  band: 'highest' | 'good' | 'possible' | 'unsure';
  band_label: string;
  match: number;
  tightness: number;
  evidence: number;
}

export interface GroupCardItem {
  id: string;
  label: string;
  confidence: GroupConfidence;
  why_chips: string[];
  photos: PhotoItem[];
  photo_count: number;
}

export interface CognitiveOptionItem {
  id: string;
  label: string;
  icon?: string;
}

export interface CognitiveCardItem {
  id: string;
  title: string;
  category: string;
  description: string;
  options: CognitiveOptionItem[];
}

export interface FollowupProbeItem {
  question: string;
  options: string[];
}

export interface QuestionOptionItem {
  id: string;
  label: string;
  cue_id?: string;
}

export interface QuestionItem {
  id: string;
  prompt: string;
  options: QuestionOptionItem[];
}

export interface SearchSessionState {
  session_id: string;
  started_at: string;
  entry: string;
  step: 'cue_board' | 'groups' | 'question' | 'almost' | 'fallback' | 'found';
  cards?: CueCardItem[];
  cognitive_cards?: CognitiveCardItem[];
  groups?: GroupCardItem[];
  clues: ClueItem[];
  question?: QuestionItem;
  found_photo_id?: string;
  followup_probes?: FollowupProbeItem[];
  preserved_context?: string[];
}

export type NudgeStage = 'initial' | 'scrolling_detected';

export interface QuestionAnswerPayload {
  session_id: string;
  question_id: string;
  option_id: string;
}



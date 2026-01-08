export interface SearchState {
  query: string;
  sessionId: string;
  status: 'idle' | 'searching' | 'completed' | 'error';
  currentStage: SearchStage | null;
  stages: SearchStageResult[];
  finalAnswer: string | null;
  error: string | null;
  startTime: number | null;
  endTime: number | null;
}

export type SearchStage =
  | 'sni_exact_query'
  | 'vector_search'
  | 'initial_web_search'
  | 'keyword_extraction'
  | 'round1_planning'
  | 'round1_search'
  | 'round2_planning'
  | 'round2_search'
  | 'final_planning'
  | 'final_search'
  | 'synthesize'
  | 'tgt_standardization';

export interface SearchStageResult {
  stage: SearchStage;
  status: 'pending' | 'in_progress' | 'completed' | 'error';
  data: Record<string, any>;
  timestamp: number;
  duration?: number;
}

export interface SNIResult {
  sni: string;
  domain: string;
  score?: number;
  protocols?: string[];
  match_count?: number;
}

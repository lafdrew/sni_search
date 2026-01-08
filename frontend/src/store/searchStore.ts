import { create } from 'zustand';
import type { SearchState, SearchStage } from '../types/search';

const STAGE_ORDER: SearchStage[] = [
  'sni_exact_query',
  'vector_search',
  'initial_web_search',
  'keyword_extraction',
  'round1_planning',
  'round1_search',
  'round2_planning',
  'round2_search',
  'final_planning',
  'final_search',
  'synthesize',
  'tgt_standardization'
];

interface SearchActions {
  startSearch: (query: string) => void;
  updateStage: (stage: SearchStage, data: Record<string, any>) => void;
  completeStage: (stage: SearchStage) => void;
  setFinalAnswer: (answer: string) => void;
  setError: (error: string) => void;
  reset: () => void;
}

export const useSearchStore = create<SearchState & SearchActions>((set) => ({
  query: '',
  sessionId: '',
  status: 'idle',
  currentStage: null,
  stages: STAGE_ORDER.map(stage => ({
    stage,
    status: 'pending' as const,
    data: {},
    timestamp: 0
  })),
  finalAnswer: null,
  error: null,
  startTime: null,
  endTime: null,

  startSearch: (query) => set({
    query,
    sessionId: crypto.randomUUID(),
    status: 'searching',
    currentStage: STAGE_ORDER[0],
    stages: STAGE_ORDER.map(stage => ({
      stage,
      status: 'pending' as const,
      data: {},
      timestamp: 0
    })),
    finalAnswer: null,
    error: null,
    startTime: Date.now(),
    endTime: null
  }),

  updateStage: (stage, data) => set(state => {
    const stages = state.stages.map(s =>
      s.stage === stage
        ? { ...s, status: 'in_progress' as const, data, timestamp: Date.now() }
        : s
    );
    return { stages, currentStage: stage };
  }),

  completeStage: (stage) => set(state => {
    const stages = state.stages.map(s => {
      if (s.stage === stage) {
        const duration = Date.now() - s.timestamp;
        return { ...s, status: 'completed' as const, duration };
      }
      return s;
    });

    const currentIndex = STAGE_ORDER.indexOf(stage);
    const nextStage = currentIndex < STAGE_ORDER.length - 1
      ? STAGE_ORDER[currentIndex + 1]
      : null;

    return {
      stages,
      currentStage: nextStage,
      status: nextStage ? 'searching' : 'completed'
    };
  }),

  setFinalAnswer: (answer) => set({
    finalAnswer: answer,
    status: 'completed',
    endTime: Date.now()
  }),

  setError: (error) => set({
    error,
    status: 'error',
    endTime: Date.now()
  }),

  reset: () => set({
    query: '',
    sessionId: '',
    status: 'idle',
    currentStage: null,
    stages: STAGE_ORDER.map(stage => ({
      stage,
      status: 'pending' as const,
      data: {},
      timestamp: 0
    })),
    finalAnswer: null,
    error: null,
    startTime: null,
    endTime: null
  })
}));

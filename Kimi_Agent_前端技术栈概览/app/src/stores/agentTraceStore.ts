import { create } from 'zustand';
import type { AgentTraceStep } from '@/types';

interface AgentTraceStore {
  // State
  steps: AgentTraceStep[];
  isExpanded: boolean;
  isVisible: boolean;
  
  // Actions
  addStep: (step: Omit<AgentTraceStep, 'id' | 'timestamp'>) => void;
  toggleExpanded: () => void;
  show: () => void;
  hide: () => void;
  clear: () => void;
  setExpanded: (expanded: boolean) => void;
}

export const useAgentTraceStore = create<AgentTraceStore>((set) => ({
  steps: [],
  isExpanded: false,
  isVisible: false,

  addStep: (step) => set((state) => ({
    steps: [
      ...state.steps,
      {
        ...step,
        id: Math.random().toString(36).substr(2, 9),
        timestamp: Date.now()
      }
    ]
  })),

  toggleExpanded: () => set((state) => ({
    isExpanded: !state.isExpanded
  })),

  setExpanded: (expanded: boolean) => set({
    isExpanded: expanded
  }),

  show: () => set({ isVisible: true }),

  hide: () => set({ isVisible: false, isExpanded: false }),

  clear: () => set({ steps: [], isExpanded: false })
}));

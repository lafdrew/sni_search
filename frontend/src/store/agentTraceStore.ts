/**
 * Agent Trace Store
 *
 * Manages the state for the Agent Trace UI, including the event stream
 * and current execution status.
 */

import { create } from 'zustand';
import type { AgentEvent } from '../types/agentEvent';

export type AgentStatus = 'idle' | 'thinking' | 'completed' | 'error';

interface AgentTraceState {
  // Core event stream
  events: AgentEvent[];

  // Session metadata
  query: string;
  sessionId: string;
  status: AgentStatus;

  // Current execution state
  currentAction: string | null;  // "Searching..." | "Analyzing..." | null

  // Locale for internationalization
  locale: string;

  // Actions
  addEvent: (event: Omit<AgentEvent, 'id' | 'timestamp'>) => void;
  addEvents: (events: Omit<AgentEvent, 'id' | 'timestamp'>[]) => void;
  clearEvents: () => void;
  setCurrentAction: (action: string | null) => void;
  setStatus: (status: AgentStatus) => void;
  startQuery: (query: string, sessionId?: string) => void;
  setLocale: (locale: string) => void;
  reset: () => void;
}

// Generate unique ID for events
function generateEventId(): string {
  return `evt_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
}

export const useAgentTraceStore = create<AgentTraceState>((set) => ({
  // Initial state
  events: [],
  query: '',
  sessionId: '',
  status: 'idle',
  currentAction: null,
  locale: 'en-US',

  // Add a single event
  addEvent: (eventInput) => set((state) => ({
    events: [
      ...state.events,
      {
        ...eventInput,
        id: generateEventId(),
        timestamp: Date.now()
      }
    ]
  })),

  // Add multiple events at once
  addEvents: (eventsInput) => set((state) => ({
    events: [
      ...state.events,
      ...eventsInput.map(eventInput => ({
        ...eventInput,
        id: generateEventId(),
        timestamp: Date.now()
      }))
    ]
  })),

  // Clear all events
  clearEvents: () => set({
    events: [],
    currentAction: null
  }),

  // Set current action (displayed as "Searching..." etc.)
  setCurrentAction: (action) => set({ currentAction: action }),

  // Set status
  setStatus: (status) => set({ status }),

  // Start a new query
  startQuery: (query, sessionId) => set({
    query,
    sessionId: sessionId || crypto.randomUUID(),
    status: 'thinking',
    events: [],
    currentAction: null
  }),

  // Set locale
  setLocale: (locale) => set({ locale }),

  // Reset everything
  reset: () => set({
    events: [],
    query: '',
    sessionId: '',
    status: 'idle',
    currentAction: null
  })
}));

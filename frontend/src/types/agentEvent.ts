/**
 * Agent Trace UI Event System
 *
 * This module defines the event types for the Agent Trace UI,
 * which provides a chat-like, streaming view of the agent's reasoning process.
 */

export type AgentEventType =
  | 'thought'           // Reasoning/thinking bubble (gray, explanatory)
  | 'search_action'     // Search behavior indicator
  | 'search_results'    // Search results list (clickable bubbles)
  | 'observation'       // Observation/analysis note
  | 'answer'            // Final answer
  | 'error';            // Error message

export interface AgentEvent {
  id: string;                    // Unique identifier
  type: AgentEventType;
  timestamp: number;
  data: {
    // thought
    content?: string;            // Thought content

    // search_action & search_results
    query?: string;              // Search query (used in search_action and search_results)
    engine?: string;             // Search engine name

    // search_results
    items?: SearchResultItem[];  // Result items

    // observation
    summary?: string;            // Observation summary

    // answer
    answer?: string;             // Final answer (JSON string)

    // error
    error?: string;              // Error message
  };
}

export type ResultType = 'web' | 'news' | 'academic' | 'commerce' | 'official';

export interface SearchResultItem {
  title: string;
  url: string;
  favicon?: string;
  snippet?: string;
  type?: ResultType;
}

// Type guard helpers
export function isThoughtEvent(event: AgentEvent): event is AgentEvent & { type: 'thought' } {
  return event.type === 'thought';
}

export function isSearchActionEvent(event: AgentEvent): event is AgentEvent & { type: 'search_action' } {
  return event.type === 'search_action';
}

export function isSearchResultsEvent(event: AgentEvent): event is AgentEvent & { type: 'search_results' } {
  return event.type === 'search_results';
}

export function isObservationEvent(event: AgentEvent): event is AgentEvent & { type: 'observation' } {
  return event.type === 'observation';
}

export function isAnswerEvent(event: AgentEvent): event is AgentEvent & { type: 'answer' } {
  return event.type === 'answer';
}

export function isErrorEvent(event: AgentEvent): event is AgentEvent & { type: 'error' } {
  return event.type === 'error';
}

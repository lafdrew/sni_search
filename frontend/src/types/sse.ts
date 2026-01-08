export type SSEEventType =
  | 'search_started'
  | 'node_sni_exact_query'
  | 'node_vector_search'
  | 'node_initial_web_search'
  | 'node_keyword_extraction'
  | 'node_round1_planning'
  | 'node_round1_search'
  | 'node_round2_planning'
  | 'node_round2_search'
  | 'node_final_planning'
  | 'node_final_search'
  | 'node_synthesize'
  | 'search_completed'
  | 'error';

export interface SSEEvent<T = any> {
  event: SSEEventType;
  data: T;
}

export interface SearchStartedData {
  query: string;
  session_id: string;
  timestamp: string;
}

export interface NodeEventData {
  node: string;
  state: Record<string, any>;
  timestamp: string;
}

export interface ErrorData {
  error: string;
  timestamp?: string;
}

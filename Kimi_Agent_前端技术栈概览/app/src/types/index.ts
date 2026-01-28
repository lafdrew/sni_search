export interface SearchResult {
  id: string;
  source: string;
  sourceIcon: string;
  title: string;
  description: string;
  url: string;
}

export interface AgentTraceStep {
  id: string;
  type: 'thinking' | 'search' | 'analyze' | 'conclude';
  content: string;
  timestamp: number;
}

export interface SearchState {
  query: string;
  isSearching: boolean;
  results: SearchResult[];
  totalCount: number;
  proMode: boolean;
}

export interface AgentTraceState {
  steps: AgentTraceStep[];
  isExpanded: boolean;
  isVisible: boolean;
}

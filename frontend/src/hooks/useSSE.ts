import { useEffect, useRef } from 'react';
import { useSearchStore } from '../store/searchStore';

export function useSSE(url: string | null) {
  const eventSourceRef = useRef<EventSource | null>(null);
  const {
    startSearch,
    updateStage,
    completeStage,
    setFinalAnswer,
    setError
  } = useSearchStore();

  useEffect(() => {
    if (!url) return;

    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      console.log('[SSE] Connection opened');
    };

    eventSource.onerror = (error) => {
      console.error('[SSE] Error:', error);
      setError('Connection error');
      eventSource.close();
    };

    // Handle search_started
    eventSource.addEventListener('search_started', (e) => {
      const data = JSON.parse(e.data);
      console.log('[SSE] Search started:', data);
      startSearch(data.query);
    });

    // Handle node events
    const stageMapping: Record<string, any> = {
      'node_sni_exact_query': 'sni_exact_query',
      'node_vector_search': 'vector_search',
      'node_initial_web_search': 'initial_web_search',
      'node_keyword_extraction': 'keyword_extraction',
      'node_round1_planning': 'round1_planning',
      'node_round1_search': 'round1_search',
      'node_round2_planning': 'round2_planning',
      'node_round2_search': 'round2_search',
      'node_final_planning': 'final_planning',
      'node_final_search': 'final_search',
      'node_synthesize': 'synthesize',
      'node_tgt_standardization': 'tgt_standardization'
    };

    Object.keys(stageMapping).forEach((eventType) => {
      eventSource.addEventListener(eventType, (e) => {
        const data = JSON.parse((e as MessageEvent).data);
        const stage = stageMapping[eventType];

        console.log(`[SSE] ${eventType}:`, data);
        updateStage(stage, data.state);

        setTimeout(() => {
          completeStage(stage);

          if (stage === 'tgt_standardization' && data.state.final_answer) {
            setFinalAnswer(data.state.final_answer);
          }
        }, 500);
      });
    });

    // Handle error event
    eventSource.addEventListener('error', (e) => {
      const data = JSON.parse((e as MessageEvent).data);
      setError(data.error);
    });

    return () => {
      console.log('[SSE] Closing connection');
      eventSource.close();
    };
  }, [url, startSearch, updateStage, completeStage, setFinalAnswer, setError]);

  const close = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
  };

  return { close };
}

/**
 * useSSE Hook
 *
 * Manages Server-Sent Events connection and transforms
 * node events into granular UI events for the Agent Trace UI
 */

import { useEffect, useRef } from 'react';
import { useAgentTraceStore } from '../store/agentTraceStore';
import { transformNodeToUIEvents } from '../utils/eventTransformer';

export function useSSE(url: string | null) {
  const eventSourceRef = useRef<EventSource | null>(null);
  const { startQuery, addEvents, setStatus, setCurrentAction, locale } = useAgentTraceStore();

  useEffect(() => {
    if (!url) return;

    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    // Track if search has completed successfully
    let searchCompleted = false;

    eventSource.onopen = () => {
      console.log('[SSE] Connection opened');
      setStatus('thinking');
    };

    eventSource.onerror = (error) => {
      // If search completed successfully, this is just the connection closing - ignore it
      if (searchCompleted) {
        console.log('[SSE] Connection closed after completion');
        eventSource.close();
        return;
      }

      // Otherwise, it's a real error
      console.error('[SSE] Error:', error);
      addEvents([{
        type: 'error',
        data: { error: 'Connection error' }
      }]);
      setStatus('error');
      eventSource.close();
    };

    // Handle search_started
    eventSource.addEventListener('search_started', (e) => {
      const data = JSON.parse(e.data);
      console.log('[SSE] Search started:', data);
      startQuery(data.query, data.session_id);
    });

    // Node event mapping
    const nodeEventTypes = [
      'node_sni_exact_query',
      'node_vector_search',
      'node_initial_web_search',
      'node_keyword_extraction',
      'node_round1_planning',
      'node_round1_search',
      'node_round2_planning',
      'node_round2_search',
      'node_final_planning',
      'node_final_search',
      'node_synthesize',
      'node_tgt_standardization'
    ];

    const nodeNameMapping: Record<string, string> = {
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

    // Register listeners for each node event type
    nodeEventTypes.forEach((eventType) => {
      eventSource.addEventListener(eventType, (e) => {
        const data = JSON.parse((e as MessageEvent).data);
        const nodeName = nodeNameMapping[eventType];

        console.log(`[SSE] ${eventType}:`, data);

        // Transform node event to UI events
        const uiEvents = transformNodeToUIEvents(nodeName, data.state, locale);

        // Add all UI events to store
        if (uiEvents.length > 0) {
          addEvents(uiEvents);
        }

        // Update current action based on node
        if (nodeName.includes('search')) {
          setCurrentAction('Searching...');
        } else if (nodeName.includes('planning') || nodeName.includes('extraction')) {
          setCurrentAction('Analyzing...');
        } else if (nodeName === 'synthesize') {
          setCurrentAction('Synthesizing...');
        }

        // Clear current action after a delay
        setTimeout(() => {
          setCurrentAction(null);
        }, 1000);
      });
    });

    // Handle search completion
    eventSource.addEventListener('search_completed', () => {
      console.log('[SSE] Search completed');
      searchCompleted = true;
      setStatus('completed');
      setCurrentAction(null);
    });

    // Handle error event
    eventSource.addEventListener('error', (e) => {
      try {
        const data = JSON.parse((e as MessageEvent).data);
        addEvents([{
          type: 'error',
          data: { error: data.error }
        }]);
      } catch {
        // Already handled in onerror
      }
    });

    return () => {
      console.log('[SSE] Closing connection');
      eventSource.close();
    };
  }, [url, startQuery, addEvents, setStatus, setCurrentAction, locale]);

  const close = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
  };

  return { close };
}

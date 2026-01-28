/**
 * EventStream Component
 *
 * Enhanced with EmptyState and better error handling inspired by Kimi Agent
 */

import { memo, useEffect, useRef } from 'react';
import { useAgentTraceStore } from '../../store/agentTraceStore';
import { ThoughtBubble } from './ThoughtBubble';
import { SearchAction } from './SearchAction';
import { SearchResults } from './SearchResults';
import { Observation } from './Observation';
import { FinalAnswerCard } from './FinalAnswerCard';
import { EmptyState } from '@/components/EmptyState';
import { ErrorDisplay } from '@/components/ErrorDisplay';
import type { AgentEvent } from '../../types/agentEvent';

export const EventStream = memo(function EventStream() {
  const events = useAgentTraceStore((state) => state.events);
  const streamEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest event
  useEffect(() => {
    if (streamEndRef.current) {
      streamEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [events.length]);

  if (events.length === 0) {
    return (
      <EmptyState
        icon="sparkles"
        title="Enter a query to start..."
        description="Ask anything and watch the AI agent work through the problem step by step"
      />
    );
  }

  return (
    <div className="space-y-6 pb-8">
      {events.map((event) => (
        <EventItem key={event.id} event={event} />
      ))}
      <div ref={streamEndRef} />
    </div>
  );
});

// Individual event renderer
const EventItem = memo(function EventItem({ event }: { event: AgentEvent }) {
  switch (event.type) {
    case 'thought':
      return <ThoughtBubble content={event.data.content || ''} />;

    case 'search_action':
      return (
        <SearchAction
          query={event.data.query || ''}
          engine={event.data.engine}
        />
      );

    case 'search_results':
      return <SearchResults items={event.data.items || []} query={event.data.query} />;

    case 'observation':
      return <Observation summary={event.data.summary || ''} />;

    case 'answer':
      return <FinalAnswerCard answer={event.data.answer || ''} />;

    case 'error':
      return (
        <ErrorDisplay
          title="Connection Error"
          message={event.data.error || 'An unexpected error occurred'}
        />
      );

    default:
      return null;
  }
});

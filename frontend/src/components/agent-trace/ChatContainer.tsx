/**
 * ChatContainer Component
 *
 * Enhanced with shadcn/ui components and Emerald theme
 */

import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Button } from '@/components/ui/button';
import { Home } from 'lucide-react';
import { Header } from './Header';
import { EventStream } from './EventStream';
import { InputComposer } from './InputComposer';
import { useSSE } from '../../hooks/useSSE';
import { useAgentTraceStore } from '../../store/agentTraceStore';
import { t, type Locale } from '../../utils/i18n';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export function ChatContainer() {
  const [sseUrl, setSSEUrl] = useState<string | null>(null);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const locale = useAgentTraceStore((state) => state.locale) as Locale;

  useSSE(sseUrl);

  const aiDisclaimerText = t('aiDisclaimer', locale);

  // Handle query from URL parameter
  useEffect(() => {
    const query = searchParams.get('q');
    if (query) {
      // Auto-submit query from URL
      handleSubmit(query);
    }
  }, [searchParams]);

  const handleSubmit = (query: string) => {
    // Build SSE URL - use /query/stream endpoint (not /query)
    const url = new URL('/query/stream', API_BASE_URL);
    url.searchParams.set('query', query);
    url.searchParams.set('verbose', 'true');

    setSSEUrl(url.toString());
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 p-6">
      <div className="max-w-5xl mx-auto">
        <Card className="h-[calc(100vh-3rem)] flex flex-col shadow-2xl border-emerald-200 dark:border-emerald-900">
          <CardHeader className="pb-3 border-b dark:border-gray-700 flex flex-row items-center justify-between">
            <Header />
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/')}
              className="gap-2"
            >
              <Home className="w-4 h-4" />
              <span className="hidden sm:inline">Home</span>
            </Button>
          </CardHeader>

          <CardContent className="flex-1 p-0 overflow-hidden">
            <ScrollArea className="h-full">
              <div className="p-6">
                <EventStream />
              </div>
            </ScrollArea>
          </CardContent>

          <Separator className="dark:bg-gray-700" />

          <div className="p-4 border-t dark:border-gray-700">
            <InputComposer onSubmit={handleSubmit} />
          </div>
        </Card>

        {/* System info footer */}
        <div className="text-center mt-6 space-y-1">
          <div className="text-[9px] text-muted-foreground">
            <span className="font-medium">SNI Agent v2.0</span>
            <span className="mx-2">•</span>
            <span>LangGraph Engine</span>
            <span className="mx-2">•</span>
            <span>Claude Powered</span>
          </div>
          <div className="text-[8px] text-muted-foreground/70">
            {aiDisclaimerText}
          </div>
        </div>
      </div>
    </div>
  );
}

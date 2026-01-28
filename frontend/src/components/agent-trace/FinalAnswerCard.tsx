/**
 * FinalAnswerCard Component
 *
 * Enhanced with Framer Motion, shadcn/ui components, and Emerald theme
 */

import { memo, useState } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Copy, Check, ChevronDown } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { cn } from '@/lib/utils';

interface FinalAnswerCardProps {
  answer: string;
}

export const FinalAnswerCard = memo(function FinalAnswerCard({ answer }: FinalAnswerCardProps) {
  const [copied, setCopied] = useState(false);
  const [showRaw, setShowRaw] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Try to parse JSON for better display
  let parsedAnswer: any = null;
  try {
    parsedAnswer = JSON.parse(answer);
  } catch {
    // Not JSON, display as-is
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className="my-8"
    >
      <Card className="border-2 border-primary/20 bg-primary/5 dark:bg-primary/10">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-primary" />
              <CardTitle className="text-lg">Final Answer</CardTitle>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="default">Complete</Badge>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleCopy}
                className="h-8 w-8"
              >
                {copied ? (
                  <Check className="w-3.5 h-3.5 text-green-500" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {parsedAnswer ? (
            <>
              {parsedAnswer.tgt && (
                <div>
                  <h4 className="text-sm font-semibold text-muted-foreground mb-1">
                    Target Service
                  </h4>
                  <p className="text-base font-medium">{parsedAnswer.tgt}</p>
                </div>
              )}

              {parsedAnswer.service_type && (
                <div>
                  <h4 className="text-sm font-semibold text-muted-foreground mb-1">
                    Service Type
                  </h4>
                  <Badge variant="secondary">{parsedAnswer.service_type}</Badge>
                </div>
              )}

              {parsedAnswer.Explanation && (
                <div>
                  <h4 className="text-sm font-semibold text-muted-foreground mb-1">
                    Explanation
                  </h4>
                  <p className="text-sm leading-relaxed">{parsedAnswer.Explanation}</p>
                </div>
              )}

              {parsedAnswer['Query Results'] && (
                <div>
                  <h4 className="text-sm font-semibold text-muted-foreground mb-1">
                    Query Results
                  </h4>
                  <p className="text-sm leading-relaxed">{parsedAnswer['Query Results']}</p>
                </div>
              )}

              <Collapsible open={showRaw} onOpenChange={setShowRaw}>
                <CollapsibleTrigger className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
                  <ChevronDown className={cn(
                    "w-4 h-4 transition-transform",
                    showRaw && "rotate-180"
                  )} />
                  <span>Raw JSON</span>
                </CollapsibleTrigger>
                <CollapsibleContent className="mt-2">
                  <pre className="text-xs bg-muted p-3 rounded-lg overflow-x-auto">
                    {JSON.stringify(parsedAnswer, null, 2)}
                  </pre>
                </CollapsibleContent>
              </Collapsible>
            </>
          ) : (
            <pre className="text-sm whitespace-pre-wrap font-mono">{answer}</pre>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
});

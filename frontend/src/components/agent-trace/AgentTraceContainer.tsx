import { useState } from 'react'
import { Brain, ChevronDown, ChevronUp } from 'lucide-react'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface AgentTraceContainerProps {
  children: React.ReactNode
  defaultExpanded?: boolean
  title?: string
  subtitle?: string
  className?: string
}

export function AgentTraceContainer({
  children,
  defaultExpanded = true,
  title = "Agent Thinking Process",
  subtitle,
  className,
}: AgentTraceContainerProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)

  return (
    <Collapsible
      open={isExpanded}
      onOpenChange={setIsExpanded}
      className={cn("w-full space-y-2", className)}
    >
      <div className="flex items-center justify-between rounded-lg border border-border/40 bg-background/50 backdrop-blur-sm px-4 py-3 transition-colors hover:bg-accent/50">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
            <Brain className="h-4 w-4" />
          </div>
          <div className="flex flex-col">
            <h3 className="text-sm font-semibold text-foreground">{title}</h3>
            {subtitle && (
              <p className="text-xs text-muted-foreground">{subtitle}</p>
            )}
          </div>
        </div>

        <CollapsibleTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            aria-label={isExpanded ? "Collapse trace" : "Expand trace"}
          >
            {isExpanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
        </CollapsibleTrigger>
      </div>

      <CollapsibleContent className="space-y-2">
        {children}
      </CollapsibleContent>
    </Collapsible>
  )
}

// Example usage:
// <AgentTraceContainer title="Agent Thinking Process" subtitle="12 steps completed">
//   <EventStream />
// </AgentTraceContainer>

/**
 * Header Component
 *
 * Enhanced with shadcn/ui components, ThemeToggle, and Emerald theme
 */

import { Activity, CheckCircle2, AlertCircle, Loader2, RotateCcw } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { ThemeToggle } from '@/components/theme-toggle';
import { useAgentTraceStore, type AgentStatus } from '../../store/agentTraceStore';

interface StatusConfig {
  icon: typeof Activity;
  label: string;
  variant: 'default' | 'secondary' | 'destructive' | 'outline';
}

const STATUS_CONFIG: Record<AgentStatus, StatusConfig> = {
  idle: { icon: Activity, label: 'Ready', variant: 'secondary' },
  thinking: { icon: Loader2, label: 'Processing', variant: 'default' },
  completed: { icon: CheckCircle2, label: 'Complete', variant: 'default' },
  error: { icon: AlertCircle, label: 'Error', variant: 'destructive' }
};

export function Header() {
  const { status, currentAction, reset } = useAgentTraceStore();

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-primary" />
          <h1 className="text-lg font-semibold text-foreground">
            SNI Agent
          </h1>
          <span className="text-xs text-muted-foreground">v2.0</span>
        </div>

        {status !== 'idle' && (
          <div className="flex items-center gap-2">
            <Separator orientation="vertical" className="h-5" />
            <StatusBadge status={status} />
            {currentAction && (
              <span className="text-sm text-muted-foreground">
                {currentAction}
              </span>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        <ThemeToggle />

        {status !== 'idle' && (
          <Button
            variant="ghost"
            size="icon"
            onClick={reset}
            className="w-9 h-9"
          >
            <RotateCcw className="w-4 h-4" />
          </Button>
        )}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: AgentStatus }) {
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;

  return (
    <Badge variant={config.variant} className="gap-1">
      <Icon className={`w-3 h-3 ${status === 'thinking' ? 'animate-spin' : ''}`} />
      {config.label}
    </Badge>
  );
}

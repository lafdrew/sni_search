/**
 * StatusIndicator Component
 *
 * Visual status indicator inspired by Kimi Agent
 */

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface StatusIndicatorProps {
  status: 'idle' | 'thinking' | 'completed' | 'error';
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  showPulse?: boolean;
  className?: string;
}

export function StatusIndicator({
  status,
  label,
  size = 'md',
  showPulse = true,
  className = ''
}: StatusIndicatorProps) {
  const sizes = {
    sm: 'w-2 h-2',
    md: 'w-3 h-3',
    lg: 'w-4 h-4'
  };

  const colors = {
    idle: 'bg-gray-400',
    thinking: 'bg-blue-500',
    completed: 'bg-emerald-500',
    error: 'bg-red-500'
  };

  const shouldPulse = showPulse && status === 'thinking';

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div className="relative">
        <div className={cn('rounded-full', sizes[size], colors[status])} />
        {shouldPulse && (
          <motion.div
            animate={{
              scale: [1, 1.5, 1],
              opacity: [0.5, 0, 0.5]
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            }}
            className={cn(
              'absolute inset-0 rounded-full',
              colors[status]
            )}
          />
        )}
      </div>
      {label && (
        <span className="text-sm text-muted-foreground">{label}</span>
      )}
    </div>
  );
}

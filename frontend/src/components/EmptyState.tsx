/**
 * EmptyState Component
 *
 * Elegant empty state display inspired by Kimi Agent
 */

import { motion } from 'framer-motion';
import { Search, MessageSquare, Sparkles } from 'lucide-react';

interface EmptyStateProps {
  icon?: 'search' | 'message' | 'sparkles';
  title?: string;
  description?: string;
  className?: string;
}

export function EmptyState({
  icon = 'search',
  title = 'Enter a query to start...',
  description,
  className = ''
}: EmptyStateProps) {
  const icons = {
    search: Search,
    message: MessageSquare,
    sparkles: Sparkles
  };

  const Icon = icons[icon];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className={`flex flex-col items-center justify-center py-16 ${className}`}
    >
      <motion.div
        initial={{ scale: 0.8 }}
        animate={{ scale: 1 }}
        transition={{
          duration: 0.5,
          delay: 0.1,
          ease: [0.34, 1.56, 0.64, 1]
        }}
        className="mb-4 p-4 bg-primary/5 dark:bg-primary/10 rounded-full"
      >
        <Icon className="w-8 h-8 text-primary" />
      </motion.div>

      <h3 className="text-2xl sm:text-3xl font-light text-muted-foreground/80 tracking-tight text-center">
        {title}
      </h3>

      {description && (
        <p className="mt-2 text-sm text-muted-foreground text-center max-w-md">
          {description}
        </p>
      )}
    </motion.div>
  );
}

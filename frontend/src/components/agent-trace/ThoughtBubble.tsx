/**
 * ThoughtBubble Component
 *
 * Enhanced with Framer Motion
 */

import { memo } from 'react';
import { motion } from 'framer-motion';
import { Cpu } from 'lucide-react';

interface ThoughtBubbleProps {
  content: string;
}

export const ThoughtBubble = memo(function ThoughtBubble({ content }: ThoughtBubbleProps) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.2 }}
      className="flex items-start gap-3 mb-3"
    >
      <Cpu className="w-4 h-4 text-muted-foreground mt-1 flex-shrink-0" />
      <p className="text-sm text-muted-foreground">{content}</p>
    </motion.div>
  );
});

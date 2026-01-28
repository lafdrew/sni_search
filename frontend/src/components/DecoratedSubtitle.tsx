import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface DecoratedSubtitleProps {
  text: string;
  className?: string;
}

export function DecoratedSubtitle({ text, className }: DecoratedSubtitleProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className={cn('flex items-center justify-center gap-4', className)}
    >
      <div className="w-12 sm:w-16 h-px bg-border dark:bg-border" />
      <p className="text-sm sm:text-base text-muted-foreground text-center">
        {text}
      </p>
      <div className="w-12 sm:w-16 h-px bg-border dark:bg-border" />
    </motion.div>
  );
}

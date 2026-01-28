/**
 * Logo Component
 *
 * Animated logo with gradient inspired by Kimi Agent
 */

import { motion } from 'framer-motion';
import { Activity } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LogoProps {
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
  className?: string;
}

const SIZE_CONFIG = {
  sm: { icon: 'w-5 h-5', text: 'text-base' },
  md: { icon: 'w-6 h-6', text: 'text-lg' },
  lg: { icon: 'w-8 h-8', text: 'text-2xl' }
} as const;

export function Logo({ size = 'md', showText = true, className }: LogoProps) {
  const config = SIZE_CONFIG[size];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className={cn('flex items-center gap-2', className)}
    >
      <div className="relative">
        <motion.div
          animate={{
            rotate: [0, 360],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: "linear"
          }}
          className="absolute inset-0 bg-gradient-to-r from-emerald-400 to-teal-500 rounded-lg opacity-20 blur-sm"
        />
        <div className="relative bg-gradient-to-br from-emerald-500 to-teal-600 p-1.5 rounded-lg">
          <Activity className={cn(config.icon, 'text-white')} strokeWidth={2.5} />
        </div>
      </div>

      {showText && (
        <span className={cn(
          config.text,
          'font-bold bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent'
        )}>
          SNI Agent
        </span>
      )}
    </motion.div>
  );
}

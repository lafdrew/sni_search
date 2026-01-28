/**
 * Logo Component
 *
 * Animated logo with gradient inspired by Kimi Agent
 */

import { motion } from 'framer-motion';
import { Activity } from 'lucide-react';

interface LogoProps {
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
  className?: string;
}

export function Logo({ size = 'md', showText = true, className = '' }: LogoProps) {
  const sizes = {
    sm: { icon: 'w-5 h-5', text: 'text-base' },
    md: { icon: 'w-6 h-6', text: 'text-lg' },
    lg: { icon: 'w-8 h-8', text: 'text-2xl' }
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className={`flex items-center gap-2 ${className}`}
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
          <Activity className={`${sizes[size].icon} text-white`} strokeWidth={2.5} />
        </div>
      </div>

      {showText && (
        <span className={`${sizes[size].text} font-bold bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent`}>
          SNI Agent
        </span>
      )}
    </motion.div>
  );
}

import { motion } from 'framer-motion';

interface GradientTitleProps {
  text: string;
  className?: string;
}

export function GradientTitle({ text, className = '' }: GradientTitleProps) {
  return (
    <motion.h1
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.6,
        ease: [0.16, 1, 0.3, 1]
      }}
      className={`text-4xl sm:text-5xl lg:text-[48px] font-bold leading-tight text-center ${className}`}
    >
      <span className="bg-gradient-to-r from-emerald-500 via-emerald-400 to-emerald-600 bg-clip-text text-transparent">
        {text}
      </span>
    </motion.h1>
  );
}

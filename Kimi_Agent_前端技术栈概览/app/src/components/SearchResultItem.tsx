import { motion } from 'framer-motion';
import { SourceIcon } from './SourceIcon';
import type { SearchResult } from '@/types';

interface SearchResultItemProps {
  result: SearchResult;
  index: number;
}

export function SearchResultItem({ result, index }: SearchResultItemProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.4,
        delay: index * 0.05,
        ease: [0.16, 1, 0.3, 1]
      }}
      className="group flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-all duration-150 hover:bg-emerald-50/50 border-l-2 border-transparent hover:border-emerald-500"
    >
      <SourceIcon source={result.sourceIcon} />
      
      <div className="flex-1 min-w-0">
        <h4 className="text-sm font-medium text-emerald-600 group-hover:text-emerald-700 truncate">
          {result.title}
        </h4>
        <p className="text-xs text-gray-500 mt-1 line-clamp-2">
          {result.description}
        </p>
      </div>
    </motion.div>
  );
}

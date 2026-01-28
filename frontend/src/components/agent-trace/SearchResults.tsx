/**
 * SearchResults Component
 *
 * Enhanced with Framer Motion stagger animation
 */

import { memo } from 'react';
import { motion } from 'framer-motion';
import { SearchHeader } from './SearchHeader';
import { ResultItem } from './ResultItem';
import { useAgentTraceStore } from '../../store/agentTraceStore';
import type { SearchResultItem } from '../../types/agentEvent';
import type { Locale } from '../../utils/i18n';

interface SearchResultsProps {
  items: SearchResultItem[];
  query?: string;
}

export const SearchResults = memo(function SearchResults({ items, query }: SearchResultsProps) {
  if (items.length === 0) return null;

  const storeQuery = useAgentTraceStore((state) => state.query);
  const locale = useAgentTraceStore((state) => state.locale) as Locale;

  // Use provided query or fallback to store query
  const displayQuery = query || storeQuery || 'search';

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{
        visible: {
          transition: { staggerChildren: 0.05 }
        }
      }}
      className="space-y-2 mt-3"
    >
      <SearchHeader query={displayQuery} count={items.length} locale={locale} />
      {items.map((item, index) => (
        <motion.div
          key={`${item.url}-${index}`}
          variants={{
            hidden: { opacity: 0, y: 10 },
            visible: { opacity: 1, y: 0 }
          }}
        >
          <ResultItem
            title={item.title}
            url={item.url}
            snippet={item.snippet}
            type={item.type}
          />
        </motion.div>
      ))}
    </motion.div>
  );
});

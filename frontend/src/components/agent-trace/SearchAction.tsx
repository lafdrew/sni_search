/**
 * SearchAction Component
 *
 * Clean search transmission indicator
 */

import { memo } from 'react';
import { Search, Zap } from 'lucide-react';

interface SearchActionProps {
  query: string;
  engine?: string;
}

export const SearchAction = memo(function SearchAction({ query, engine = 'Web' }: SearchActionProps) {
  return (
    <div className="flex justify-center animate-fade-in opacity-0 my-6">
      <div className="relative max-w-3xl w-full">
        {/* Main indicator */}
        <div className="flex items-center gap-5 px-6 py-4 bg-slate-50/60 backdrop-blur-md rounded-2xl shadow-md">
          {/* Left icon */}
          <div className="flex items-center gap-2.5">
            <Search className="w-5 h-5 text-slate-600" strokeWidth={2.5} />
            <span className="text-[11px] text-slate-600 uppercase tracking-wider font-medium">
              Searching
            </span>
          </div>

          {/* Query */}
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <span className="text-slate-400">▸</span>
            <span className="text-base text-charcoal-700 font-semibold tracking-wide truncate leading-relaxed">
              {query}
            </span>
          </div>

          {/* Engine badge */}
          {engine && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-warning-50/80 backdrop-blur-sm rounded-lg flex-shrink-0 shadow-sm">
              <Zap className="w-3 h-3 text-warning-600" strokeWidth={2.5} />
              <span className="text-[10px] text-warning-700 font-semibold uppercase tracking-wider">
                {engine}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
});

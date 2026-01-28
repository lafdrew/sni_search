/**
 * Observation Component
 *
 * Clean observation log with success styling
 */

import { memo } from 'react';
import { CheckSquare } from 'lucide-react';

interface ObservationProps {
  summary: string;
}

export const Observation = memo(function Observation({ summary }: ObservationProps) {
  return (
    <div className="flex justify-center animate-fade-in opacity-0" style={{ animationDelay: '100ms' }}>
      <div className="flex items-start gap-4 max-w-3xl w-full px-5 py-4 bg-success-50/60 backdrop-blur-sm border-l-4 border-success-300 rounded-xl shadow-sm">
        {/* Icon */}
        <div className="flex-shrink-0 pt-1">
          <CheckSquare className="w-4 h-4 text-success-600" strokeWidth={2.5} />
        </div>

        {/* Content - 三段式 */}
        <div className="flex-1 space-y-2">
          {/* 标签 */}
          <span className="text-[10px] text-success-600 uppercase tracking-wider font-medium">
            Log
          </span>

          {/* 内容 */}
          <div className="text-base text-success-900 leading-relaxed">
            {summary}
          </div>
        </div>
      </div>
    </div>
  );
});

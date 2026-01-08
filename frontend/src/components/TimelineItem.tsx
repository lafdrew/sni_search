import { useState, useEffect } from 'react';
import { ChevronDown, ChevronRight, Loader2, CheckCircle2, Clock } from 'lucide-react';
import type { SearchStageResult } from '../types/search';

interface TimelineItemProps {
  stage: SearchStageResult;
  label: string;
  isLast: boolean;
  index?: number; // 添加索引用于动画延迟
}

export function TimelineItem({ stage, label, isLast, index = 0 }: TimelineItemProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isVisible, setIsVisible] = useState(false);

  // 当项目首次出现时触发动画
  useEffect(() => {
    if (stage.status !== 'pending') {
      setIsVisible(true);
    }
  }, [stage.status]);

  const getStatusIcon = () => {
    switch (stage.status) {
      case 'in_progress':
        return (
          <div className="relative">
            <Loader2 className="w-5 h-5 text-[#007AFF] animate-smooth-spin" strokeWidth={2.5} />
            <div className="absolute inset-0 w-5 h-5 rounded-full bg-[#007AFF] opacity-10 animate-gentle-pulse" />
          </div>
        );
      case 'completed':
        return (
          <div className="relative">
            <CheckCircle2 className="w-5 h-5 text-[#34C759]" strokeWidth={2.5} fill="rgba(52, 199, 89, 0.1)" />
          </div>
        );
      default:
        return (
          <Clock className="w-5 h-5 text-[#D2D2D7]" strokeWidth={2} />
        );
    }
  };

  const hasData = Object.keys(stage.data).length > 0;

  // 如果还没开始，不渲染
  if (!isVisible) {
    return null;
  }

  return (
    <div
      className="relative animate-fade-in opacity-0"
      style={{ animationDelay: `${index * 0.1}s` }}
    >
      {/* Connector Line */}
      {!isLast && (
        <div className="absolute left-[19px] top-10 w-0.5 h-full bg-gradient-to-b from-[#E5E5EA] to-transparent" />
      )}

      <div className="flex items-start gap-4">
        {/* Status Icon */}
        <div className="flex-shrink-0 relative z-10">
          <div className={`flex items-center justify-center w-10 h-10 rounded-full transition-all duration-300 ${
            stage.status === 'completed'
              ? 'bg-[#F0FDF4] border-2 border-[#34C759]'
              : stage.status === 'in_progress'
              ? 'bg-[#F0F9FF] border-2 border-[#007AFF] shadow-lg shadow-[#007AFF]/20'
              : 'bg-white border-2 border-[#E5E5EA]'
          }`}>
            {getStatusIcon()}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0 pb-8">
          {/* Header */}
          <div
            className={`flex items-center justify-between py-3 px-4 rounded-xl transition-all duration-200 ${
              hasData
                ? 'cursor-pointer hover:bg-white hover:shadow-sm'
                : 'cursor-default'
            }`}
            onClick={() => hasData && setIsExpanded(!isExpanded)}
          >
            <div className="flex-1">
              <h4 className={`text-sm font-medium transition-colors ${
                stage.status === 'completed'
                  ? 'text-[#1D1D1F]'
                  : stage.status === 'in_progress'
                  ? 'text-[#007AFF]'
                  : 'text-[#86868B]'
              }`}>
                {label}
              </h4>
              {stage.duration && (
                <p className="text-xs text-[#86868B] mt-0.5 font-mono">
                  {stage.duration}ms
                </p>
              )}
            </div>

            {/* Expand/Collapse Icon */}
            {hasData && (
              <div className="flex-shrink-0 ml-3 transition-transform duration-200">
                {isExpanded ? (
                  <ChevronDown className="w-5 h-5 text-[#86868B]" strokeWidth={2.5} />
                ) : (
                  <ChevronRight className="w-5 h-5 text-[#86868B]" strokeWidth={2.5} />
                )}
              </div>
            )}
          </div>

          {/* Expandable Content */}
          {isExpanded && hasData && (
            <div className="mt-2 p-4 bg-white rounded-xl border border-[#E5E5EA] shadow-sm animate-scale-in">
              <pre className="text-xs overflow-auto text-[#1D1D1F] font-mono leading-relaxed">
                {JSON.stringify(stage.data, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

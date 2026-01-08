import { useSearchStore } from '../store/searchStore';
import { TimelineItem } from './TimelineItem';
import { STAGE_LABELS } from '../utils/constants';

export function SearchTimeline() {
  const { stages } = useSearchStore();

  // 只显示已经开始的阶段（不是 pending 状态）
  const visibleStages = stages.filter(s => s.status !== 'pending');

  const completedCount = stages.filter(s => s.status === 'completed').length;
  const progress = (completedCount / stages.length) * 100;

  return (
    <div className="w-full max-w-3xl mx-auto space-y-6">
      {/* Progress Card */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-[#E5E5EA]">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-[#86868B]">Search Progress</h3>
          <span className="text-sm font-semibold text-[#007AFF]">
            {Math.round(progress)}%
          </span>
        </div>

        {/* Progress Bar */}
        <div className="relative h-2 bg-[#F5F5F7] rounded-full overflow-hidden">
          <div
            className="absolute inset-y-0 left-0 bg-gradient-to-r from-[#007AFF] to-[#0051D5] rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          >
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
          </div>
        </div>

        <div className="flex items-center justify-between mt-2 text-xs text-[#86868B]">
          <span>{completedCount} of {stages.length} stages completed</span>
        </div>
      </div>

      {/* Timeline - 只显示已开始的阶段 */}
      {visibleStages.length > 0 && (
        <div className="space-y-1">
          {visibleStages.map((stage, visibleIndex) => {
            // 计算在原始数组中的位置，用于判断是否是最后一个可见项
            const originalIndex = stages.findIndex(s => s.stage === stage.stage);
            const isLastVisible = originalIndex === stages.length - 1;

            return (
              <TimelineItem
                key={stage.stage}
                stage={stage}
                label={STAGE_LABELS[stage.stage]}
                isLast={isLastVisible}
                index={visibleIndex} // 传递可见索引用于动画延迟
              />
            );
          })}
        </div>
      )}
    </div>
  );
}

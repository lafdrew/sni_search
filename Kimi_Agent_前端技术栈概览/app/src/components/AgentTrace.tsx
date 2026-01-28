import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Brain, Search, MessageSquare } from 'lucide-react';
import { useAgentTraceStore } from '@/stores/agentTraceStore';
import { useEffect } from 'react';
import { useSearchStore } from '@/stores/searchStore';

export function AgentTrace() {
  const { steps, isExpanded, isVisible, toggleExpanded, addStep, show, clear } = useAgentTraceStore();
  const { isSearching, query } = useSearchStore();

  useEffect(() => {
    if (isSearching && query) {
      show();
      clear();
      
      // 模拟添加思考步骤
      const timer1 = setTimeout(() => {
        addStep({
          type: 'thinking',
          content: `The user says "${query}". That's likely Chinese name "Wang Haoge"? Or "${query}" might be a name or a phrase. The user might be asking about this name, maybe searching for a person with that name. We need to figure out the...`
        });
      }, 300);

      const timer2 = setTimeout(() => {
        addStep({
          type: 'search',
          content: `搜索: "${query}"`
        });
      }, 600);

      const timer3 = setTimeout(() => {
        addStep({
          type: 'analyze',
          content: `找到 19 个结果`
        });
      }, 900);

      return () => {
        clearTimeout(timer1);
        clearTimeout(timer2);
        clearTimeout(timer3);
      };
    }
  }, [isSearching, query, addStep, show, clear]);

  if (!isVisible) {
    return null;
  }

  const getStepIcon = (type: string) => {
    switch (type) {
      case 'thinking':
        return <Brain className="w-4 h-4 text-amber-500" />;
      case 'search':
        return <Search className="w-4 h-4 text-blue-500" />;
      case 'analyze':
        return <MessageSquare className="w-4 h-4 text-green-500" />;
      default:
        return <MessageSquare className="w-4 h-4 text-gray-500" />;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.3 }}
      className="w-full max-w-3xl mx-auto mt-4"
    >
      <div className="bg-slate-50 border border-gray-200 rounded-xl overflow-hidden">
        {/* 头部 - 可点击展开 */}
        <button
          onClick={toggleExpanded}
          className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-100 transition-colors duration-150"
        >
          <div className="flex items-center gap-2">
            <Brain className="w-4 h-4 text-emerald-500" />
            <span className="text-sm font-medium text-gray-700">Agent 思考过程</span>
            {steps.length > 0 && (
              <span className="text-xs text-gray-500">({steps.length} 个步骤)</span>
            )}
          </div>
          <motion.div
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronDown className="w-4 h-4 text-gray-400" />
          </motion.div>
        </button>

        {/* 展开内容 */}
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
              className="overflow-hidden"
            >
              <div className="px-4 pb-4 space-y-3">
                {steps.map((step, index) => (
                  <motion.div
                    key={step.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-start gap-3"
                  >
                    <div className="mt-0.5">{getStepIcon(step.type)}</div>
                    <div className="flex-1">
                      <p className="text-sm text-gray-600 leading-relaxed">
                        {step.content}
                      </p>
                      <span className="text-xs text-gray-400 mt-1">
                        {new Date(step.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  </motion.div>
                ))}
                
                {steps.length === 0 && (
                  <p className="text-sm text-gray-400 text-center py-4">
                    等待开始搜索...
                  </p>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

import { motion, AnimatePresence } from 'framer-motion';
import { Search, X } from 'lucide-react';
import { SearchResultItem } from './SearchResultItem';
import { useSearchStore } from '@/stores/searchStore';
import { ScrollArea } from '@/components/ui/scroll-area';

export function SearchResults() {
  const { query, results, totalCount, clearResults, isSearching } = useSearchStore();

  if (results.length === 0 && !isSearching) {
    return null;
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
        className="w-full max-w-3xl mx-auto mt-8"
      >
        <div className="bg-white rounded-2xl shadow-[0_4px_20px_rgba(0,0,0,0.08)] overflow-hidden">
          {/* 头部 */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
            <div className="flex items-center gap-2">
              <Search className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-600">
                搜索: "{query}"
              </span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-500">
                找到 {totalCount} 个结果
              </span>
              <button
                onClick={clearResults}
                className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors duration-150"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* 结果列表 */}
          <ScrollArea className="max-h-[400px]">
            <div className="p-2">
              {isSearching ? (
                // 加载状态
                <div className="flex items-center justify-center py-12">
                  <div className="flex items-center gap-3">
                    <div className="w-5 h-5 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
                    <span className="text-sm text-gray-500">搜索中...</span>
                  </div>
                </div>
              ) : (
                // 结果列表
                <div className="space-y-1">
                  {results.map((result, index) => (
                    <SearchResultItem
                      key={result.id}
                      result={result}
                      index={index}
                    />
                  ))}
                </div>
              )}
            </div>
          </ScrollArea>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}

/**
 * SearchHeader Component
 *
 * Displays search query and result count above search results
 * MiroMind-style header with clean typography
 */

import { memo } from 'react';
import { t, getResultCountText, type Locale } from '../../utils/i18n';

interface SearchHeaderProps {
  query: string;
  count: number;
  locale?: Locale;
}

export const SearchHeader = memo(function SearchHeader({
  query,
  count,
  locale = 'en-US'
}: SearchHeaderProps) {
  const searchText = t('search', locale);
  const resultCountText = getResultCountText(count, locale);

  return (
    <div className="bg-slate-50/60 backdrop-blur-sm px-5 py-6 animate-fade-in rounded-t-xl">
      {/* 三段式：标题 - 查询 - 状态 */}

      {/* 标题 */}
      <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-3 font-medium">
        {searchText}
      </div>

      {/* 查询内容 */}
      <div className="text-2xl text-charcoal-800 mb-4 font-semibold leading-relaxed">
        "{query}"
      </div>

      {/* 状态 */}
      <div className="text-sm text-slate-500 leading-relaxed">
        {resultCountText}
      </div>
    </div>
  );
});

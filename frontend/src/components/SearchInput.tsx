import React from 'react';
import { Search, X } from 'lucide-react';
import { useSearch } from '../hooks/useSearch';

export function SearchInput() {
  const { query, setQuery, startSearch, stopSearch, isSearching } = useSearch();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    startSearch();
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-3xl mx-auto">
      <div className="relative flex items-center gap-3 p-2 bg-white rounded-2xl shadow-lg hover:shadow-xl transition-shadow duration-300">
        {/* Search Icon */}
        <div className="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-blue-50 to-blue-100">
          <Search className="w-5 h-5 text-[#007AFF]" strokeWidth={2.5} />
        </div>

        {/* Input Field */}
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search for an SNI..."
          className="flex-1 px-4 py-3 text-base bg-transparent border-0 outline-none text-[#1D1D1F] placeholder-[#86868B] transition-all"
          disabled={isSearching}
        />

        {/* Clear Button */}
        {query && !isSearching && (
          <button
            type="button"
            onClick={() => setQuery('')}
            className="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full hover:bg-gray-100 transition-colors duration-200"
          >
            <X className="w-4 h-4 text-[#86868B]" strokeWidth={2.5} />
          </button>
        )}

        {/* Search Button */}
        <button
          type="submit"
          disabled={isSearching || !query.trim()}
          className="flex-shrink-0 px-6 py-3 bg-[#007AFF] text-white font-medium rounded-xl hover:bg-[#0051D5] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-[#007AFF] transition-all duration-200 flex items-center gap-2 shadow-sm hover:shadow-md active:scale-95"
        >
          {isSearching ? (
            <>
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <span className="hidden sm:inline">Searching...</span>
            </>
          ) : (
            <>
              <Search className="w-4 h-4" strokeWidth={2.5} />
              <span>Search</span>
            </>
          )}
        </button>

        {/* Stop Button */}
        {isSearching && (
          <button
            type="button"
            onClick={stopSearch}
            className="flex-shrink-0 px-5 py-3 bg-white text-[#FF3B30] font-medium rounded-xl border border-[#FFE5E5] hover:bg-[#FFF5F5] hover:border-[#FFD1D1] transition-all duration-200 active:scale-95"
          >
            Stop
          </button>
        )}
      </div>

      {/* Helper Text */}
      <p className="mt-3 text-sm text-center text-[#86868B]">
        Enter a domain name or SNI to identify the service
      </p>
    </form>
  );
}

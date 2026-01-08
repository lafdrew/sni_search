import { useState } from 'react';
import { useSearchStore } from '../store/searchStore';
import { useSSE } from './useSSE';

export function useSearch() {
  const [query, setQuery] = useState('');
  const { status, reset } = useSearchStore();
  const [sseUrl, setSSEUrl] = useState<string | null>(null);

  const { close } = useSSE(sseUrl);

  const startSearch = () => {
    if (!query.trim()) return;

    reset();

    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const url = `${apiUrl}/query/stream?query=${encodeURIComponent(query)}`;
    setSSEUrl(url);
  };

  const stopSearch = () => {
    close();
    setSSEUrl(null);
    reset();
  };

  return {
    query,
    setQuery,
    startSearch,
    stopSearch,
    status,
    isSearching: status === 'searching'
  };
}

import { create } from 'zustand'
import type { SearchResult } from '@/types/search'

interface SearchStore {
  // State
  query: string
  isSearching: boolean
  results: SearchResult[]
  totalCount: number
  proMode: boolean
  
  // Actions
  setQuery: (query: string) => void
  setProMode: (enabled: boolean) => void
  search: () => Promise<void>
  clearResults: () => void
}

// Mock search results for demonstration
const mockResults: SearchResult[] = [
  {
    id: '1',
    source: 'Qdrant Vector DB',
    sourceIcon: 'database',
    title: 'SNI Exact Match: example.com',
    description: 'Found exact match in vector database with 100% confidence...',
    url: '#'
  },
  {
    id: '2',
    source: 'Web Search',
    sourceIcon: 'search',
    title: 'example.com - Domain Information',
    description: 'Example domain for illustrative examples in documents...',
    url: 'https://example.com'
  },
  {
    id: '3',
    source: 'TGT Library',
    sourceIcon: 'library',
    title: 'Standardized Entity: Example Organization',
    description: 'Canonical name mapping and entity standardization data...',
    url: '#'
  }
]

export const useSearchStore = create<SearchStore>((set, get) => ({
  query: '',
  isSearching: false,
  results: [],
  totalCount: 0,
  proMode: false,

  setQuery: (query: string) => set({ query }),

  setProMode: (enabled: boolean) => set({ proMode: enabled }),

  search: async () => {
    const { query } = get()
    if (!query.trim()) return

    set({ isSearching: true })

    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 800))

    // Use mock data
    set({
      results: mockResults,
      totalCount: mockResults.length,
      isSearching: false
    })
  },

  clearResults: () => set({
    results: [],
    totalCount: 0,
    query: ''
  })
}))

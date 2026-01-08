import { SearchInput } from './components/SearchInput';
import { SearchTimeline } from './components/SearchTimeline';
import { ResultDisplay } from './components/ResultDisplay';
import { useSearchStore } from './store/searchStore';
import { Globe } from 'lucide-react';

function App() {
  const { status } = useSearchStore();

  return (
    <div className="min-h-screen bg-[#F5F5F7]">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-[#E5E5EA]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo & Title */}
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-[#007AFF] to-[#0051D5] shadow-lg shadow-[#007AFF]/30">
                <Globe className="w-5 h-5 text-white" strokeWidth={2.5} />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-[#1D1D1F] tracking-tight">
                  SNI Search
                </h1>
                <p className="text-xs text-[#86868B] hidden sm:block">
                  Real-time multi-stage recognition
                </p>
              </div>
            </div>

            {/* Status Badge */}
            {status !== 'idle' && (
              <div className="flex items-center gap-2 px-3 py-1.5 bg-[#F5F5F7] rounded-full">
                <div className={`w-2 h-2 rounded-full ${
                  status === 'completed'
                    ? 'bg-[#34C759]'
                    : 'bg-[#007AFF] animate-gentle-pulse'
                }`} />
                <span className="text-xs font-medium text-[#1D1D1F] capitalize">
                  {status === 'completed' ? 'Ready' : status}
                </span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="space-y-12">
          {/* Search Section */}
          <section className="animate-fade-in">
            <SearchInput />
          </section>

          {/* Timeline Section */}
          {status !== 'idle' && (
            <section className="animate-fade-in">
              <SearchTimeline />
            </section>
          )}

          {/* Results Section */}
          {status === 'completed' && (
            <section className="animate-fade-in">
              <ResultDisplay />
            </section>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#E5E5EA] bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-sm text-[#86868B]">
              Powered by LangGraph & Claude
            </p>
            <div className="flex items-center gap-6 text-sm text-[#86868B]">
              <span className="hidden sm:inline">•</span>
              <span>Multi-round Search Workflow</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;

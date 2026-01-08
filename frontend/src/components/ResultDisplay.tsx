import { useSearchStore } from '../store/searchStore';
import { FinalAnswer } from './FinalAnswer';
import { FileSearch, Code } from 'lucide-react';

export function ResultDisplay() {
  const { finalAnswer, stages, status } = useSearchStore();

  if (status === 'idle') {
    return (
      <div className="w-full max-w-3xl mx-auto text-center py-16 animate-fade-in opacity-0">
        <div className="inline-flex items-center justify-center w-16 h-16 mb-4 rounded-2xl bg-gradient-to-br from-blue-50 to-blue-100">
          <FileSearch className="w-8 h-8 text-[#007AFF]" strokeWidth={2} />
        </div>
        <h3 className="text-lg font-semibold text-[#1D1D1F] mb-2">
          Ready to Search
        </h3>
        <p className="text-[#86868B]">
          Enter an SNI above to start the recognition process
        </p>
      </div>
    );
  }

  const searchStages = stages.filter(stage =>
    stage.stage.includes('search') && stage.stage !== 'sni_exact_query'
  );

  return (
    <div className="w-full max-w-3xl mx-auto space-y-6">
      {/* Final Answer */}
      {finalAnswer && <FinalAnswer answer={finalAnswer} />}

      {/* Search Results */}
      {searchStages.map((stage, index) => {
        if (stage.status !== 'completed' || !stage.data) return null;

        return (
          <div
            key={stage.stage}
            className="bg-white rounded-2xl shadow-sm border border-[#E5E5EA] p-6 animate-fade-in opacity-0"
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-gray-50 to-gray-100">
                <Code className="w-5 h-5 text-[#86868B]" strokeWidth={2} />
              </div>
              <div>
                <h3 className="text-base font-semibold text-[#1D1D1F]">
                  {stage.stage.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </h3>
                {stage.duration && (
                  <p className="text-xs text-[#86868B] mt-0.5">
                    Completed in {stage.duration}ms
                  </p>
                )}
              </div>
            </div>

            <div className="mt-4 p-4 bg-[#F5F5F7] rounded-xl border border-[#E5E5EA] overflow-auto">
              <pre className="text-xs text-[#1D1D1F] font-mono leading-relaxed">
                {JSON.stringify(stage.data, null, 2)}
              </pre>
            </div>
          </div>
        );
      })}
    </div>
  );
}

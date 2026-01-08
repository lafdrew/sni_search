import { Copy, CheckCircle2 } from 'lucide-react';
import { useState } from 'react';

interface FinalAnswerProps {
  answer: string;
}

export function FinalAnswer({ answer }: FinalAnswerProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(answer);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  let parsed: any = null;

  try {
    parsed = JSON.parse(answer);
  } catch (e) {
    return (
      <div className="bg-white rounded-2xl shadow-sm border border-[#E5E5EA] p-6 animate-fade-in opacity-0">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-[#1D1D1F]">Final Answer</h2>
          <button
            onClick={handleCopy}
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-[#007AFF] hover:bg-[#E5F1FF] rounded-lg transition-colors"
          >
            {copied ? (
              <>
                <CheckCircle2 className="w-4 h-4" strokeWidth={2.5} />
                <span>Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" strokeWidth={2.5} />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
        <div className="prose max-w-none">
          <pre className="whitespace-pre-wrap text-sm text-[#1D1D1F] leading-relaxed font-mono bg-[#F5F5F7] rounded-xl p-4 overflow-auto">
            {answer}
          </pre>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-[#E5E5EA] p-6 animate-fade-in opacity-0">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-[#1D1D1F]">Recognition Result</h2>
        <button
          onClick={handleCopy}
          className="flex items-center gap-2 px-3 py-1.5 text-sm text-[#007AFF] hover:bg-[#E5F1FF] rounded-lg transition-colors"
        >
          {copied ? (
            <>
              <CheckCircle2 className="w-4 h-4" strokeWidth={2.5} />
              <span>Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-4 h-4" strokeWidth={2.5} />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      <div className="space-y-5">
        {/* Target Field */}
        <div className="group">
          <span className="text-xs font-medium text-[#86868B] uppercase tracking-wide">Target</span>
          <div className="mt-2 p-4 bg-gradient-to-br from-[#E5F1FF] to-[#F0F9FF] rounded-xl border border-[#007AFF]/20">
            <p className="text-2xl font-bold text-[#007AFF]">{parsed.tgt}</p>
          </div>
        </div>

        {/* Explanation Field */}
        {parsed.explanation && (
          <div>
            <span className="text-xs font-medium text-[#86868B] uppercase tracking-wide">Explanation</span>
            <div className="mt-2 p-4 bg-[#F5F5F7] rounded-xl">
              <p className="text-sm text-[#1D1D1F] leading-relaxed">{parsed.explanation}</p>
            </div>
          </div>
        )}

        {/* Query Results Field */}
        {parsed.queryResults && (
          <div>
            <span className="text-xs font-medium text-[#86868B] uppercase tracking-wide">Query Results</span>
            <div className="mt-2 p-4 bg-[#F5F5F7] rounded-xl border border-[#E5E5EA]">
              <p className="text-sm text-[#1D1D1F] leading-relaxed whitespace-pre-wrap font-mono">
                {parsed.queryResults}
              </p>
            </div>
          </div>
        )}

        {/* Metadata */}
        {parsed._tgt_metadata && (
          <div className="pt-4 border-t border-[#E5E5EA]">
            <div className="flex items-center gap-2 text-xs text-[#86868B]">
              <CheckCircle2 className="w-4 h-4 text-[#34C759]" strokeWidth={2.5} />
              <span>Match type: <strong className="text-[#1D1D1F]">{parsed._tgt_metadata.match_type}</strong></span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

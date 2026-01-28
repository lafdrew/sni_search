import { GradientTitle } from '@/components/GradientTitle';
import { DecoratedSubtitle } from '@/components/DecoratedSubtitle';
import { SmartInput } from '@/components/SmartInput';
import { SearchResults } from '@/components/SearchResults';
import { AgentTrace } from '@/components/AgentTrace';

export function HeroSection() {
  return (
    <section className="min-h-screen flex flex-col items-center justify-center px-4 sm:px-6 lg:px-8 py-12 bg-gradient-to-b from-white to-gray-50/50">
      <div className="w-full max-w-3xl mx-auto">
        {/* 标题区域 */}
        <div className="text-center mb-8">
          <GradientTitle 
            text="Engineered for Deep Understanding, Not Small Talk" 
            className="mb-6"
          />
          <DecoratedSubtitle 
            text="Don't just chat. Predict, verify, and discover with science-based AI." 
          />
        </div>

        {/* 输入框区域 */}
        <div className="mt-10">
          <SmartInput placeholder="比特币会在 2026 年达到 2" />
        </div>

        {/* Agent Trace */}
        <AgentTrace />

        {/* 搜索结果 */}
        <SearchResults />
      </div>
    </section>
  );
}

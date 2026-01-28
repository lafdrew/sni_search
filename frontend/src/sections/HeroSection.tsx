/**
 * HeroSection Component
 *
 * Landing page with gradient title, subtitle, input, and example queries
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { GradientTitle } from '@/components/GradientTitle';
import { DecoratedSubtitle } from '@/components/DecoratedSubtitle';
import { ExampleQueries } from '@/components/ExampleQueries';
import { Button } from '@/components/ui/button';
import { Send, Sparkles } from 'lucide-react';
import { Logo } from '@/components/Logo';
import { useAgentTraceStore } from '../store/agentTraceStore';
import { t, type Locale } from '../utils/i18n';

export function HeroSection() {
  const [input, setInput] = useState('');
  const navigate = useNavigate();
  const locale = useAgentTraceStore((state) => state.locale) as Locale;

  const handleSubmit = () => {
    const trimmed = input.trim();
    if (!trimmed) return;

    // Navigate to chat with query parameter
    navigate(`/chat?q=${encodeURIComponent(trimmed)}`);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <section className="min-h-screen flex flex-col bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Top Navigation */}
      <nav className="w-full px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
            className="flex items-center gap-3"
          >
            <Logo size="sm" />
            <div>
              <h1 className="text-lg font-bold text-foreground">SNI Agent</h1>
              <p className="text-xs text-muted-foreground">v2.0</p>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
            className="flex items-center gap-2"
          >
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/chat')}
            >
              Go to Chat
            </Button>
          </motion.div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center px-4 sm:px-6 lg:px-8 py-12">
        <div className="w-full max-w-3xl mx-auto">
          {/* Hero Text */}
          <div className="text-center mb-10">
            <GradientTitle
              text="Intelligent SNI Domain Recognition"
              className="mb-6"
            />
            <DecoratedSubtitle
              text="Multi-round search • Vector database • LangGraph powered"
            />
          </div>

          {/* Feature Highlights */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10"
          >
            {[
              { icon: '🎯', title: 'Exact Match', desc: 'Qdrant vector DB' },
              { icon: '🔍', title: '4-2-1 Search', desc: 'Multi-round strategy' },
              { icon: '🤖', title: 'LangGraph', desc: 'Deterministic flow' }
            ].map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3, delay: 0.5 + index * 0.1 }}
                className="bg-white/60 dark:bg-gray-800/60 backdrop-blur-sm rounded-xl p-4 border border-gray-200 dark:border-gray-700 text-center"
              >
                <div className="text-3xl mb-2">{feature.icon}</div>
                <h3 className="text-sm font-semibold text-foreground mb-1">
                  {feature.title}
                </h3>
                <p className="text-xs text-muted-foreground">{feature.desc}</p>
              </motion.div>
            ))}
          </motion.div>

          {/* Input Area */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{
              duration: 0.5,
              delay: 0.4,
              ease: [0.34, 1.56, 0.64, 1]
            }}
            className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-xl border-2 border-gray-200 dark:border-gray-700 hover:border-primary dark:hover:border-primary transition-all duration-200"
          >
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={t('enterQuery', locale)}
              className="w-full min-h-[120px] p-5 resize-none outline-none text-foreground placeholder:text-muted-foreground bg-transparent rounded-t-2xl"
              rows={3}
            />

            {/* Bottom Toolbar */}
            <div className="flex items-center justify-between px-5 py-3 border-t border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-primary" />
                <span className="text-xs text-muted-foreground font-medium">
                  Powered by Claude & LangGraph
                </span>
              </div>

              {/* Send Button */}
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button
                  onClick={handleSubmit}
                  disabled={!input.trim()}
                  size="default"
                  className="rounded-xl gap-2"
                >
                  <Send className="w-4 h-4" />
                  <span className="hidden sm:inline">Search</span>
                </Button>
              </motion.div>
            </div>
          </motion.div>

          {/* Example Queries */}
          <ExampleQueries />

          {/* Footer Info */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 1 }}
            className="mt-12 text-center"
          >
            <p className="text-xs text-muted-foreground">
              12-node workflow • Real-time SSE streaming • Multi-language support
            </p>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

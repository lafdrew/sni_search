/**
 * InputComposer Component
 *
 * Enhanced with Framer Motion and shadcn/ui components (Pro toggle removed)
 */

import { useState, useRef, useEffect, type KeyboardEvent } from 'react';
import { motion } from 'framer-motion';
import { Send, Loader2, Paperclip } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useAgentTraceStore } from '../../store/agentTraceStore';
import { t, type Locale } from '../../utils/i18n';

interface InputComposerProps {
  onSubmit: (query: string) => void;
}

export function InputComposer({ onSubmit }: InputComposerProps) {
  const [input, setInput] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const status = useAgentTraceStore((state) => state.status);
  const locale = useAgentTraceStore((state) => state.locale) as Locale;

  const isDisabled = status === 'thinking';

  const placeholderText = t('enterQuery', locale);
  const submitText = t('submit', locale);
  const newLineText = t('newLine', locale);

  // Auto-grow textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [input]);

  const handleSubmit = () => {
    const trimmed = input.trim();
    if (!trimmed || isDisabled) return;

    onSubmit(trimmed);
    setInput('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleFileUpload = () => {
    // TODO: Implement file upload functionality
    console.log('File upload feature - to be implemented');
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className={cn(
        "relative bg-background rounded-2xl border-2 transition-all",
        isFocused
          ? "border-primary ring-4 ring-primary/10"
          : "border-border"
      )}>
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          onKeyDown={handleKeyDown}
          placeholder={placeholderText}
          disabled={isDisabled}
          rows={1}
          className="w-full p-4 bg-transparent resize-none outline-none text-foreground placeholder:text-muted-foreground disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ minHeight: '52px', maxHeight: '200px' }}
        />

        <div className="flex items-center justify-between px-4 py-3 border-t border-border">
          <div className="text-xs text-muted-foreground flex items-center gap-3">
            <span className="flex items-center gap-1.5">
              <kbd className="px-2 py-0.5 border rounded text-[10px] bg-muted">Enter</kbd>
              <span>{submitText}</span>
            </span>
            <span>•</span>
            <span className="flex items-center gap-1.5">
              <kbd className="px-2 py-0.5 border rounded text-[10px] bg-muted">Shift+Enter</kbd>
              <span>{newLineText}</span>
            </span>
          </div>

          <div className="flex items-center gap-2">
            {/* File Upload Button */}
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Button
                onClick={handleFileUpload}
                disabled={isDisabled}
                size="icon"
                variant="ghost"
                className="rounded-xl"
                title="Upload file"
              >
                <Paperclip className="w-4 h-4" />
              </Button>
            </motion.div>

            {/* Send Button */}
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Button
                onClick={handleSubmit}
                disabled={isDisabled || !input.trim()}
                size="icon"
                className="rounded-xl"
              >
                {isDisabled ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </Button>
            </motion.div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

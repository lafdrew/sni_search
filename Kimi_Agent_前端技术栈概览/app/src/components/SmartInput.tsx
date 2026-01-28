import { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Paperclip, Send } from 'lucide-react';
import { Switch } from '@/components/ui/switch';
import { useSearchStore } from '@/stores/searchStore';

interface SmartInputProps {
  placeholder?: string;
}

export function SmartInput({ placeholder = '输入您的问题...' }: SmartInputProps) {
  const [inputValue, setInputValue] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  const { 
    setQuery, 
    search, 
    isSearching, 
    proMode, 
    setProMode 
  } = useSearchStore();

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setInputValue(value);
    setQuery(value);
  };

  const handleSubmit = async () => {
    if (!inputValue.trim() || isSearching) return;
    await search();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{
        duration: 0.5,
        delay: 0.4,
        ease: [0.34, 1.56, 0.64, 1]
      }}
      className={`relative bg-white rounded-2xl shadow-sm transition-all duration-200 ${
        isFocused 
          ? 'ring-2 ring-emerald-500 ring-offset-0 shadow-[0_0_0_4px_rgba(16,185,129,0.1)]' 
          : 'border border-gray-200'
      }`}
    >
      <textarea
        ref={textareaRef}
        value={inputValue}
        onChange={handleInputChange}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className="w-full min-h-[100px] p-5 resize-none outline-none text-gray-700 placeholder:text-gray-400 bg-transparent rounded-t-2xl"
        rows={3}
      />
      
      {/* 底部工具栏 */}
      <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
        {/* Pro 切换 */}
        <div className="flex items-center gap-2">
          <Switch
            checked={proMode}
            onCheckedChange={setProMode}
            className="data-[state=checked]:bg-emerald-500"
          />
          <span className="text-sm text-gray-500 font-medium">Pro</span>
        </div>

        {/* 右侧按钮组 */}
        <div className="flex items-center gap-2">
          {/* 附件按钮 */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors duration-150"
          >
            <Paperclip className="w-5 h-5" />
          </motion.button>

          {/* 发送按钮 */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleSubmit}
            disabled={!inputValue.trim() || isSearching}
            className={`p-2 rounded-lg transition-all duration-150 ${
              inputValue.trim() && !isSearching
                ? 'bg-emerald-500 text-white hover:bg-emerald-600'
                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
            }`}
          >
            <Send className="w-5 h-5" />
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
}

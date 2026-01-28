import { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { Paperclip, Send } from 'lucide-react'
import { Switch } from '@/components/ui/switch'
import { useSearchStore } from '@/store/searchStore'

interface SmartInputProps {
  placeholder?: string
}

export function SmartInput({ placeholder = '输入 SNI 域名进行查询...' }: SmartInputProps) {
  const [inputValue, setInputValue] = useState('')
  const [isFocused, setIsFocused] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  
  const { 
    setQuery, 
    search, 
    isSearching, 
    proMode, 
    setProMode 
  } = useSearchStore()

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value
    setInputValue(value)
    setQuery(value)
  }

  const handleSubmit = async () => {
    if (!inputValue.trim() || isSearching) return
    await search()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleFileUpload = () => {
    // TODO: Implement file upload functionality
    console.log('File upload clicked')
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{
        duration: 0.5,
        delay: 0.4,
        ease: [0.34, 1.56, 0.64, 1]
      }}
      className="relative bg-white dark:bg-gray-900 rounded-2xl shadow-sm transition-all duration-200"
      style={{
        ...(isFocused && {
          boxShadow: '0 0 0 4px rgba(16,185,129,0.1)'
        })
      }}
    >
      <textarea
        ref={textareaRef}
        value={inputValue}
        onChange={handleInputChange}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className="w-full min-h-[100px] p-5 resize-none outline-none text-gray-700 dark:text-gray-200 placeholder:text-gray-400 dark:placeholder:text-gray-500 bg-transparent rounded-t-2xl"
        rows={3}
      />
      
      <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100 dark:border-gray-800">
        <div className="flex items-center gap-2">
          <Switch
            checked={proMode}
            onCheckedChange={setProMode}
          />
          <span className="text-sm text-gray-500 dark:text-gray-400 font-medium">
            Deep Analysis
          </span>
        </div>

        <div className="flex items-center gap-2">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleFileUpload}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors duration-150"
            title="Upload file"
          >
            <Paperclip className="w-5 h-5" />
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleSubmit}
            disabled={!inputValue.trim() || isSearching}
            className="p-2 rounded-lg transition-all duration-150 bg-emerald-500 text-white hover:bg-emerald-600 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed"
            title="Send (Enter)"
          >
            <Send className="w-5 h-5" />
          </motion.button>
        </div>
      </div>
    </motion.div>
  )
}

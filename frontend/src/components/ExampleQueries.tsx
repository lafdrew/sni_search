/**
 * ExampleQueries Component
 *
 * Displays example queries that users can click to start searching
 */

import { motion } from 'framer-motion';
import { Search, Globe, Database, FileSearch } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface ExampleQuery {
  icon: React.ComponentType<{ className?: string }>;
  text: string;
  description: string;
  query: string;
}

const examples: ExampleQuery[] = [
  {
    icon: Globe,
    text: 'Video Streaming SNI',
    description: 'Bilibili video API domain',
    query: 'api.bilibili.com'
  },
  {
    icon: Database,
    text: 'Cloud Service SNI',
    description: 'Tencent Cloud CDN domain',
    query: 'cloud.tencent.com'
  },
  {
    icon: FileSearch,
    text: 'E-commerce SNI',
    description: 'Taobao API domain',
    query: 'api.m.taobao.com'
  },
  {
    icon: Search,
    text: 'Social Media SNI',
    description: 'WeChat API domain',
    query: 'api.weixin.qq.com'
  }
];

export function ExampleQueries() {
  const navigate = useNavigate();

  const handleQueryClick = (query: string) => {
    // Navigate to chat with query parameter
    navigate(`/chat?q=${encodeURIComponent(query)}`);
  };

  return (
    <div className="mt-12">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.6 }}
        className="text-center mb-6"
      >
        <p className="text-sm font-medium text-muted-foreground">
          Try these examples
        </p>
      </motion.div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {examples.map((example, index) => {
          const Icon = example.icon;
          return (
            <motion.button
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                duration: 0.4,
                delay: 0.7 + index * 0.1,
                ease: [0.16, 1, 0.3, 1]
              }}
              whileHover={{ scale: 1.02, translateY: -2 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => handleQueryClick(example.query)}
              className="group relative bg-white dark:bg-gray-800 rounded-xl p-4 border-2 border-gray-200 dark:border-gray-700 hover:border-primary dark:hover:border-primary transition-all duration-200 text-left shadow-sm hover:shadow-md"
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-primary/10 dark:bg-primary/20 flex items-center justify-center group-hover:bg-primary/20 dark:group-hover:bg-primary/30 transition-colors">
                  <Icon className="w-5 h-5 text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-semibold text-foreground mb-1">
                    {example.text}
                  </h3>
                  <p className="text-xs text-muted-foreground line-clamp-1">
                    {example.description}
                  </p>
                  <p className="text-xs text-primary/70 dark:text-primary/60 mt-2 font-mono">
                    "{example.query}"
                  </p>
                </div>
              </div>

              {/* Hover indicator */}
              <div className="absolute inset-0 rounded-xl ring-2 ring-primary/0 group-hover:ring-primary/20 transition-all pointer-events-none" />
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}

/**
 * ResultItem Component
 *
 * Enhanced with Framer Motion and Card component
 */

import { memo } from 'react';
import { motion } from 'framer-motion';
import { ExternalLink, Globe, FileText, Newspaper, ShoppingBag, GraduationCap } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import type { ResultType } from '../../types/agentEvent';

interface ResultItemProps {
  title: string;
  url: string;
  snippet?: string;
  type?: ResultType;
}

/**
 * Get icon and color based on result type
 */
function getIconConfig(type: ResultType = 'web', domain: string) {
  // Heuristic type detection if type not provided
  if (!type || type === 'web') {
    // Academic domains
    if (domain.includes('.edu') || domain.includes('scholar') || domain.includes('arxiv')) {
      return {
        Icon: GraduationCap,
        colorClass: 'text-blue-600 dark:text-blue-400'
      };
    }
    // News domains
    if (domain.includes('news') || domain.includes('times') || domain.includes('post')) {
      return {
        Icon: Newspaper,
        colorClass: 'text-red-600 dark:text-red-400'
      };
    }
    // Commerce domains
    if (domain.includes('shop') || domain.includes('store') || domain.includes('buy')) {
      return {
        Icon: ShoppingBag,
        colorClass: 'text-orange-600 dark:text-orange-400'
      };
    }
    // Government/official domains
    if (domain.includes('.gov') || domain.includes('official')) {
      return {
        Icon: FileText,
        colorClass: 'text-green-600 dark:text-green-400'
      };
    }
  }

  // Type-based configuration
  switch (type) {
    case 'news':
      return {
        Icon: Newspaper,
        colorClass: 'text-red-600 dark:text-red-400'
      };
    case 'academic':
      return {
        Icon: GraduationCap,
        colorClass: 'text-blue-600 dark:text-blue-400'
      };
    case 'commerce':
      return {
        Icon: ShoppingBag,
        colorClass: 'text-orange-600 dark:text-orange-400'
      };
    case 'official':
      return {
        Icon: FileText,
        colorClass: 'text-green-600 dark:text-green-400'
      };
    case 'web':
    default:
      return {
        Icon: Globe,
        colorClass: 'text-primary'
      };
  }
}

export const ResultItem = memo(function ResultItem({ title, url, snippet, type }: ResultItemProps) {
  const domain = new URL(url).hostname.replace('www.', '');
  const { Icon, colorClass } = getIconConfig(type, domain);

  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      transition={{ duration: 0.15 }}
    >
      <Card className="hover:border-primary/50 transition-colors cursor-pointer">
        <CardContent className="p-3">
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-start gap-2 group"
          >
            <Icon className={`w-4 h-4 ${colorClass} flex-shrink-0 mt-0.5`} />
            <div className="flex-1 space-y-1 min-w-0">
              <h4 className="text-sm font-medium group-hover:text-primary transition-colors line-clamp-1">
                {title}
              </h4>
              {snippet && (
                <p className="text-xs text-muted-foreground line-clamp-2">
                  {snippet}
                </p>
              )}
              <p className="text-xs text-muted-foreground truncate">
                {domain}
              </p>
            </div>
            <ExternalLink className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0 mt-0.5" />
          </a>
        </CardContent>
      </Card>
    </motion.div>
  );
});

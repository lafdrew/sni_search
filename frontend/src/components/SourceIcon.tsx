import {
  Search,
  Video,
  MessageCircle,
  Tv,
  Building2,
  FileText,
  Music,
  Globe
} from 'lucide-react';

interface SourceIconProps {
  source: string;
  className?: string;
}

const sourceIconMap: Record<string, React.ElementType> = {
  'sogou': Search,
  'iqiyi': Video,
  'weibo': MessageCircle,
  'manman': Tv,
  'tvmao': Tv,
  'tianyancha': Building2,
  '2345': FileText,
  'baidu': Search,
  'douyin': Music,
  'default': Globe
};

const sourceColorMap: Record<string, string> = {
  'sogou': 'text-orange-500',
  'iqiyi': 'text-green-500',
  'weibo': 'text-red-500',
  'manman': 'text-blue-500',
  'tvmao': 'text-purple-500',
  'tianyancha': 'text-blue-600',
  '2345': 'text-yellow-500',
  'baidu': 'text-blue-500',
  'douyin': 'text-pink-500',
  'default': 'text-gray-500'
};

export function SourceIcon({ source, className = '' }: SourceIconProps) {
  const Icon = sourceIconMap[source] || sourceIconMap.default;
  const colorClass = sourceColorMap[source] || sourceColorMap.default;

  return (
    <div className={`flex items-center justify-center w-5 h-5 ${className}`}>
      <Icon className={`w-4 h-4 ${colorClass}`} />
    </div>
  );
}

import { create } from 'zustand';
import type { SearchResult } from '@/types';

interface SearchStore {
  // State
  query: string;
  isSearching: boolean;
  results: SearchResult[];
  totalCount: number;
  proMode: boolean;
  
  // Actions
  setQuery: (query: string) => void;
  setProMode: (enabled: boolean) => void;
  search: () => Promise<void>;
  clearResults: () => void;
}

// 模拟搜索结果数据
const mockResults: SearchResult[] = [
  {
    id: '1',
    source: '搜狗百科',
    sourceIcon: 'sogou',
    title: '王浩歌 - 搜狗百科',
    description: '王浩歌，中国内地男演员，毕业于中央戏剧学院表演系...',
    url: 'https://baike.sogou.com/...'
  },
  {
    id: '2',
    source: '爱奇艺泡泡',
    sourceIcon: 'iqiyi',
    title: '王浩歌明星资料大全-王浩歌动态_王浩歌电视剧电影-爱奇艺泡泡',
    description: '爱奇艺泡泡为您提供王浩歌明星资料大全，包括王浩歌动态、王浩歌电视剧电影等信息...',
    url: 'https://www.iqiyi.com/...'
  },
  {
    id: '3',
    source: '新浪微博',
    sourceIcon: 'weibo',
    title: '王浩歌超话—新浪微博超话社区',
    description: '王浩歌超话，阅读数：1.2亿，帖子数：5.6万，粉丝数：8.9万...',
    url: 'https://weibo.com/...'
  },
  {
    id: '4',
    source: '漫漫看',
    sourceIcon: 'manman',
    title: '超新星全运会王浩歌视频_图片-漫漫看综艺节目',
    description: '漫漫看综艺为您提供超新星全运会王浩歌视频、图片等相关内容...',
    url: 'https://www.manmanapp.com/...'
  },
  {
    id: '5',
    source: '电视猫',
    sourceIcon: 'tvmao',
    title: '王浩歌个人资料简介,主演的电视剧电影,图片,写真_明星_电视猫',
    description: '电视猫为您提供王浩歌个人资料简介，王浩歌主演的电视剧电影等信息...',
    url: 'https://www.tvmao.com/...'
  },
  {
    id: '6',
    source: '天眼查',
    sourceIcon: 'tianyancha',
    title: '王浩歌-深圳市恩旭科技有限公司-个人简介 / 法定代表人 / 高管 / 股东 - 天眼查',
    description: '天眼查为您提供王浩歌相关的个人简介、法定代表人、高管、股东等商业信息...',
    url: 'https://www.tianyancha.com/...'
  },
  {
    id: '7',
    source: '2345明星资料大全',
    sourceIcon: '2345',
    title: '王浩歌个人资料简介_王浩歌主演的电影电视剧全集_王浩歌影视作品 - 2345明星资料大全',
    description: '2345明星资料大全为您提供王浩歌个人资料简介、主演的电影电视剧全集等...',
    url: 'https://star.2345.com/...'
  },
  {
    id: '8',
    source: '天眼查',
    sourceIcon: 'tianyancha',
    title: '王浩歌 - 法定代表人/高管/股东 - 杭州希水生物科技有限公司 - 天眼查',
    description: '天眼查为您提供王浩歌在杭州希水生物科技有限公司的法定代表人、高管、股东等商业信息...',
    url: 'https://www.tianyancha.com/...'
  },
  {
    id: '9',
    source: '百度百科',
    sourceIcon: 'baidu',
    title: '《跨年歌》李昌明词,刘书先曲,浩歌演唱',
    description: '《跨年歌》是由李昌明作词、刘书先作曲、浩歌演唱的一首歌曲...',
    url: 'https://baike.baidu.com/...'
  },
  {
    id: '10',
    source: '百度百科',
    sourceIcon: 'baidu',
    title: '王浩歌_百度百科',
    description: '王浩歌，中国内地男演员，出生于1995年，毕业于中央戏剧学院...',
    url: 'https://baike.baidu.com/...'
  },
  {
    id: '11',
    source: '抖音',
    sourceIcon: 'douyin',
    title: '王浩歌的主页',
    description: '王浩歌的抖音主页，粉丝数：12.5万，获赞数：89.6万...',
    url: 'https://www.douyin.com/...'
  }
];

export const useSearchStore = create<SearchStore>((set, get) => ({
  query: '',
  isSearching: false,
  results: [],
  totalCount: 0,
  proMode: false,

  setQuery: (query: string) => set({ query }),

  setProMode: (enabled: boolean) => set({ proMode: enabled }),

  search: async () => {
    const { query } = get();
    if (!query.trim()) return;

    set({ isSearching: true });

    // 模拟 API 调用延迟
    await new Promise(resolve => setTimeout(resolve, 800));

    // 使用模拟数据
    set({
      results: mockResults,
      totalCount: mockResults.length,
      isSearching: false
    });
  },

  clearResults: () => set({
    results: [],
    totalCount: 0,
    query: ''
  })
}));

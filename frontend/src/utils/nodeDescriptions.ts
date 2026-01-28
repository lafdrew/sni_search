/**
 * Node Descriptions for Agent Trace UI
 *
 * Provides human-readable descriptions for each workflow node
 * in both English and Chinese.
 */

export interface NodeDescription {
  name: string;
  thoughts: {
    start: string;
    analyzing?: string;
    completed?: string;
  };
  observations?: {
    found?: string;
    notFound?: string;
    extracted?: string;
  };
}

export interface LocaleDescriptions {
  [nodeName: string]: NodeDescription;
}

// English descriptions
export const NODE_DESCRIPTIONS_EN: LocaleDescriptions = {
  sni_exact_query: {
    name: 'Exact Match Search',
    thoughts: {
      start: 'Searching for exact match in database...',
      completed: 'Database search complete'
    },
    observations: {
      found: 'Found exact match in database',
      notFound: 'No exact match found, proceeding to vector search...'
    }
  },
  vector_search: {
    name: 'Vector Similarity Search',
    thoughts: {
      start: 'Performing vector similarity search...',
      analyzing: 'Analyzing semantic matches...'
    },
    observations: {
      found: 'Found similar entries',
      notFound: 'No similar entries found, initiating web search...'
    }
  },
  initial_web_search: {
    name: 'Initial Web Search',
    thoughts: {
      start: 'Starting direct web search for SNI domain...'
    }
  },
  keyword_extraction: {
    name: 'Keyword Extraction',
    thoughts: {
      start: 'Analyzing initial search results...',
      analyzing: 'Extracting key information and entities...'
    },
    observations: {
      extracted: 'Identified keywords'
    }
  },
  round1_planning: {
    name: 'Round 1 Planning',
    thoughts: {
      start: 'Generating diverse search queries...',
      analyzing: 'Planning multi-angle search strategy...'
    },
    observations: {
      extracted: 'Generated search queries'
    }
  },
  round1_search: {
    name: 'Round 1 Search',
    thoughts: {
      start: 'Executing parallel searches (Round 1)...'
    }
  },
  round2_planning: {
    name: 'Round 2 Planning',
    thoughts: {
      start: 'Analyzing Round 1 results...',
      analyzing: 'Extracting focused keywords for deeper search...'
    },
    observations: {
      extracted: 'Identified focused keywords'
    }
  },
  round2_search: {
    name: 'Round 2 Search',
    thoughts: {
      start: 'Executing focused searches (Round 2)...'
    }
  },
  final_planning: {
    name: 'Final Search Planning',
    thoughts: {
      start: 'Synthesizing all findings...',
      analyzing: 'Generating comprehensive verification query...'
    }
  },
  final_search: {
    name: 'Final Verification Search',
    thoughts: {
      start: 'Performing final verification search...'
    }
  },
  synthesize: {
    name: 'Result Synthesis',
    thoughts: {
      start: 'Consolidating all sources...',
      analyzing: 'Structuring final answer...'
    }
  },
  tgt_standardization: {
    name: 'Entity Standardization',
    thoughts: {
      start: 'Standardizing entity names...',
      analyzing: 'Matching against TGT library...'
    }
  }
};

// Chinese descriptions
export const NODE_DESCRIPTIONS_ZH: LocaleDescriptions = {
  sni_exact_query: {
    name: '精确匹配搜索',
    thoughts: {
      start: '正在数据库中查找精确匹配...',
      completed: '数据库搜索完成'
    },
    observations: {
      found: '在数据库中找到精确匹配',
      notFound: '未找到精确匹配，继续向量搜索...'
    }
  },
  vector_search: {
    name: '向量相似度搜索',
    thoughts: {
      start: '正在执行向量相似度搜索...',
      analyzing: '正在分析语义匹配结果...'
    },
    observations: {
      found: '找到相似条目',
      notFound: '未找到相似条目，开始网络搜索...'
    }
  },
  initial_web_search: {
    name: '初始网络搜索',
    thoughts: {
      start: '正在对 SNI 域名进行直接网络搜索...'
    }
  },
  keyword_extraction: {
    name: '关键词提取',
    thoughts: {
      start: '正在分析初步搜索结果...',
      analyzing: '正在提取关键信息和实体...'
    },
    observations: {
      extracted: '识别出关键词'
    }
  },
  round1_planning: {
    name: '第一轮搜索规划',
    thoughts: {
      start: '正在生成多样化搜索查询...',
      analyzing: '正在规划多角度搜索策略...'
    },
    observations: {
      extracted: '生成了搜索查询'
    }
  },
  round1_search: {
    name: '第一轮搜索',
    thoughts: {
      start: '正在执行并行搜索（第一轮）...'
    }
  },
  round2_planning: {
    name: '第二轮搜索规划',
    thoughts: {
      start: '正在分析第一轮搜索结果...',
      analyzing: '正在提取聚焦关键词进行深度搜索...'
    },
    observations: {
      extracted: '识别出聚焦关键词'
    }
  },
  round2_search: {
    name: '第二轮搜索',
    thoughts: {
      start: '正在执行聚焦搜索（第二轮）...'
    }
  },
  final_planning: {
    name: '最终搜索规划',
    thoughts: {
      start: '正在综合所有发现...',
      analyzing: '正在生成综合验证查询...'
    }
  },
  final_search: {
    name: '最终验证搜索',
    thoughts: {
      start: '正在执行最终验证搜索...'
    }
  },
  synthesize: {
    name: '结果综合',
    thoughts: {
      start: '正在整合所有信息源...',
      analyzing: '正在构建最终答案...'
    }
  },
  tgt_standardization: {
    name: '实体标准化',
    thoughts: {
      start: '正在标准化实体名称...',
      analyzing: '正在匹配 TGT 标准库...'
    }
  }
};

// Helper function to get descriptions by locale
export function getNodeDescriptions(locale: string = 'en-US'): LocaleDescriptions {
  if (locale.startsWith('zh')) {
    return NODE_DESCRIPTIONS_ZH;
  }
  return NODE_DESCRIPTIONS_EN;
}

export function getNodeDescription(nodeName: string, locale: string = 'en-US'): NodeDescription | undefined {
  const descriptions = getNodeDescriptions(locale);
  return descriptions[nodeName];
}

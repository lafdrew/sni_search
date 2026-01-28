/**
 * Event Transformer
 *
 * Transforms backend node events into granular UI events
 * for the Agent Trace UI.
 */

import type { AgentEvent } from '../types/agentEvent';
import { getNodeDescription } from './nodeDescriptions';

// Omit id and timestamp since they will be generated when adding to store
export type UIEventInput = Omit<AgentEvent, 'id' | 'timestamp'>;

/**
 * Transform a node event from the backend into one or more UI events
 */
export function transformNodeToUIEvents(
  nodeName: string,
  state: Record<string, any>,
  locale: string = 'en-US'
): UIEventInput[] {
  const description = getNodeDescription(nodeName, locale);
  const events: UIEventInput[] = [];

  switch (nodeName) {
    case 'sni_exact_query':
      // Start thought
      events.push({
        type: 'thought',
        data: { content: description?.thoughts.start || 'Searching database...' }
      });

      // Observation based on result
      // sni_exact_results is an object with {found, match_count, matches}
      if (state.sni_exact_results?.found && state.sni_exact_results?.match_count > 0) {
        const count = state.sni_exact_results.match_count;
        events.push({
          type: 'observation',
          data: {
            summary: `${description?.observations?.found || 'Found exact match in database'} (${count} ${count === 1 ? 'match' : 'matches'})`
          }
        });
      } else {
        events.push({
          type: 'observation',
          data: { summary: description?.observations?.notFound || 'No exact match found, continuing search...' }
        });
      }
      break;

    case 'vector_search':
      events.push({
        type: 'thought',
        data: { content: description?.thoughts.start || 'Performing vector search...' }
      });

      // sni_vector_results might be an array or object
      const hasVectorResults = Array.isArray(state.sni_vector_results)
        ? state.sni_vector_results.length > 0
        : state.sni_vector_results?.found && state.sni_vector_results?.match_count > 0;

      if (hasVectorResults) {
        events.push({
          type: 'observation',
          data: { summary: description?.observations?.found || 'Found similar entries' }
        });
      } else {
        events.push({
          type: 'observation',
          data: { summary: description?.observations?.notFound || 'No similar entries found, starting web search...' }
        });
      }
      break;

    case 'initial_web_search':
      events.push({
        type: 'thought',
        data: { content: description?.thoughts.start || 'Starting web search...' }
      });

      if (state.initial_search_query) {
        events.push({
          type: 'search_action',
          data: {
            query: state.initial_search_query,
            engine: 'Web'
          }
        });
      }

      // Extract URLs from initial search result with query
      if (state.initial_search_result) {
        const urls = extractUrlsFromSearchResult(state.initial_search_result);
        if (urls.length > 0) {
          events.push({
            type: 'search_results',
            data: {
              items: urls,
              query: state.initial_search_query || state.query
            }
          });
        }
      }
      break;

    case 'keyword_extraction':
      events.push({
        type: 'thought',
        data: { content: description?.thoughts.start || 'Analyzing search results...' }
      });

      if (state.extracted_keywords && state.extracted_keywords.length > 0) {
        const keywords = state.extracted_keywords.join(', ');
        events.push({
          type: 'observation',
          data: {
            summary: `${description?.observations?.extracted || 'Identified keywords'}: ${keywords}`
          }
        });
      }

      if (state.enhanced_query) {
        events.push({
          type: 'thought',
          data: { content: locale.startsWith('zh') ? '将生成多角度搜索查询...' : 'Generating multi-angle search queries...' }
        });
      }
      break;

    case 'round1_planning':
      events.push({
        type: 'thought',
        data: { content: description?.thoughts.start || 'Planning round 1 searches...' }
      });

      if (state.round1_queries && state.round1_queries.length > 0) {
        events.push({
          type: 'observation',
          data: {
            summary: `${description?.observations?.extracted || 'Generated'} ${state.round1_queries.length} ${locale.startsWith('zh') ? '个搜索查询' : 'search queries'}`
          }
        });
      }
      break;

    case 'round1_search':
      events.push({
        type: 'thought',
        data: { content: description?.thoughts.start || 'Executing round 1 searches...' }
      });

      // Generate events for each round1 search
      if (state.round1_results && Array.isArray(state.round1_results)) {
        state.round1_results.forEach((result: any) => {
          if (result.query) {
            events.push({
              type: 'search_action',
              data: {
                query: result.query,
                engine: 'Web'
              }
            });
          }

          // Extract URLs from result with query
          const urls = extractUrlsFromSearchResult(result.result || result);
          if (urls.length > 0) {
            events.push({
              type: 'search_results',
              data: {
                items: urls,
                query: result.query || state.query
              }
            });
          }
        });
      }
      break;

    case 'round2_planning':
      events.push({
        type: 'thought',
        data: { content: description?.thoughts.start || 'Analyzing round 1 results...' }
      });

      if (state.round2_keywords && state.round2_keywords.length > 0) {
        const keywords = state.round2_keywords.join(', ');
        events.push({
          type: 'observation',
          data: {
            summary: `${description?.observations?.extracted || 'Identified focused keywords'}: ${keywords}`
          }
        });
      }
      break;

    case 'round2_search':
      events.push({
        type: 'thought',
        data: { content: description?.thoughts.start || 'Executing round 2 searches...' }
      });

      // Generate events for each round2 search
      if (state.round2_results && Array.isArray(state.round2_results)) {
        state.round2_results.forEach((result: any) => {
          if (result.keyword) {
            events.push({
              type: 'search_action',
              data: {
                query: result.keyword,
                engine: 'Web'
              }
            });
          }

          const urls = extractUrlsFromSearchResult(result.result || result);
          if (urls.length > 0) {
            events.push({
              type: 'search_results',
              data: {
                items: urls,
                query: result.keyword || state.query
              }
            });
          }
        });
      }
      break;

    case 'final_planning':
      events.push({
        type: 'thought',
        data: { content: description?.thoughts.start || 'Synthesizing findings...' }
      });

      if (state.final_search_query) {
        events.push({
          type: 'observation',
          data: {
            summary: locale.startsWith('zh')
              ? '生成了综合验证查询'
              : 'Generated comprehensive verification query'
          }
        });
      }
      break;

    case 'final_search':
      events.push({
        type: 'thought',
        data: { content: description?.thoughts.start || 'Performing final search...' }
      });

      if (state.final_search_query) {
        events.push({
          type: 'search_action',
          data: {
            query: state.final_search_query,
            engine: 'Web'
          }
        });
      }

      if (state.final_search_result) {
        const urls = extractUrlsFromSearchResult(state.final_search_result);
        if (urls.length > 0) {
          events.push({
            type: 'search_results',
            data: {
              items: urls,
              query: state.final_search_query || state.query
            }
          });
        }
      }
      break;

    case 'synthesize':
      events.push({
        type: 'thought',
        data: { content: description?.thoughts.start || 'Consolidating all sources...' }
      });

      // In synthesize node, backend returns raw_answer (not final_answer yet)
      // The final_answer comes from tgt_standardization node
      if (state.raw_answer) {
        events.push({
          type: 'observation',
          data: { summary: locale.startsWith('zh') ? '生成初步答案' : 'Generated preliminary answer' }
        });
      }
      break;

    case 'tgt_standardization':
      // Only add events if TGT standardization actually happened
      if (state.tgt_metadata && Object.keys(state.tgt_metadata).length > 0) {
        events.push({
          type: 'thought',
          data: { content: description?.thoughts.start || 'Standardizing entities...' }
        });

        events.push({
          type: 'observation',
          data: {
            summary: locale.startsWith('zh')
              ? '已完成实体标准化'
              : 'Entity standardization completed'
          }
        });
      }

      // Display final answer from tgt_standardization node
      if (state.final_answer) {
        events.push({
          type: 'answer',
          data: { answer: state.final_answer }
        });
      }
      break;

    default:
      // Fallback for unknown nodes
      events.push({
        type: 'thought',
        data: { content: `Processing: ${nodeName}` }
      });
  }

  return events;
}

/**
 * Extract URLs from search result data
 * Handles various result formats from different search engines
 */
function extractUrlsFromSearchResult(result: any): Array<{ title: string; url: string; snippet?: string }> {
  const urls: Array<{ title: string; url: string; snippet?: string }> = [];

  if (!result) return urls;

  // Handle string result (might contain URLs)
  if (typeof result === 'string') {
    // Try to extract URLs from text using regex
    const urlRegex = /https?:\/\/[^\s]+/g;
    const matches = result.match(urlRegex);
    if (matches) {
      matches.slice(0, 5).forEach(url => {
        urls.push({ title: url, url });
      });
    }
    return urls;
  }

  // Handle array of results
  if (Array.isArray(result)) {
    result.slice(0, 5).forEach(item => {
      if (item.url || item.link) {
        urls.push({
          title: item.title || item.url || item.link,
          url: item.url || item.link,
          snippet: item.snippet || item.description
        });
      }
    });
    return urls;
  }

  // Handle object with results array
  if (result.results && Array.isArray(result.results)) {
    result.results.slice(0, 5).forEach((item: any) => {
      if (item.url || item.link) {
        urls.push({
          title: item.title || item.url || item.link,
          url: item.url || item.link,
          snippet: item.snippet || item.description
        });
      }
    });
    return urls;
  }

  // Handle object with urls array
  if (result.urls && Array.isArray(result.urls)) {
    result.urls.slice(0, 5).forEach((url: string | { url: string; title?: string }) => {
      if (typeof url === 'string') {
        urls.push({ title: url, url });
      } else if (url.url) {
        urls.push({
          title: url.title || url.url,
          url: url.url
        });
      }
    });
  }

  return urls;
}

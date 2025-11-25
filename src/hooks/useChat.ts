'use client';

import { useState, useCallback } from 'react';
import { ChatMessage, EconomicData, QueryIntent } from '@/lib/types';
import { interpretQuery, getSimilarCountries, getSimilarIndicators } from '@/lib/query-interpreter';
import { fetchWorldBankData, fetchRegionalAverage, getCountryRegion } from '@/lib/api/worldbank';
import { generateNarrative } from '@/lib/narrative';
import { REGIONAL_CODES } from '@/lib/constants';

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [lastData, setLastData] = useState<EconomicData | null>(null);

  const addMessage = useCallback((message: Omit<ChatMessage, 'id' | 'timestamp'>) => {
    const newMessage: ChatMessage = {
      ...message,
      id: Math.random().toString(36).substring(7),
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, newMessage]);
    return newMessage.id;
  }, []);

  const updateMessage = useCallback((id: string, updates: Partial<ChatMessage>) => {
    setMessages(prev =>
      prev.map(msg => (msg.id === id ? { ...msg, ...updates } : msg))
    );
  }, []);

  const processQuery = useCallback(async (query: string) => {
    // Add user message
    addMessage({ role: 'user', content: query });

    // Add loading message
    const loadingId = addMessage({ role: 'assistant', content: '', isLoading: true });

    setIsLoading(true);

    try {
      // Interpret the query
      const intent = interpretQuery(query);

      // Handle ambiguous queries
      if (intent.isAmbiguous) {
        let clarification = intent.clarificationNeeded || 'Could you please clarify your question?';

        // Suggest similar matches if no country found
        if (intent.countries.length === 0) {
          const queryWords = query.toLowerCase().split(' ');
          for (const word of queryWords) {
            if (word.length > 3) {
              const similar = getSimilarCountries(word);
              if (similar.length > 0) {
                clarification += `\n\nDid you mean: ${similar.join(', ')}?`;
                break;
              }
            }
          }
        }

        // Suggest indicators if none found
        if (!intent.indicator) {
          const similarIndicators = getSimilarIndicators(query);
          if (similarIndicators.length > 0) {
            clarification += `\n\nAvailable indicators include: ${similarIndicators.map(i => i.name).join(', ')}.`;
          }
        }

        updateMessage(loadingId, {
          content: clarification,
          isLoading: false,
        });
        setIsLoading(false);
        return;
      }

      // Fetch data
      const countryCodes = intent.countries.map(c => c.iso3);
      const indicatorCode = intent.indicator!.code;

      const data = await fetchWorldBankData(
        countryCodes,
        indicatorCode,
        intent.startYear,
        intent.endYear
      );

      // Try to get regional average for comparison
      let regionalData;
      if (intent.countries.length === 1 && !Object.values(REGIONAL_CODES).includes(countryCodes[0])) {
        // Get the country's region
        const regionCode = await getCountryRegion(countryCodes[0]);
        if (regionCode) {
          regionalData = await fetchRegionalAverage(
            regionCode,
            indicatorCode,
            intent.startYear,
            intent.endYear
          );
        }
      }

      // Generate narrative
      const narrative = generateNarrative(data, regionalData);

      // Build response content
      let content = narrative.summary;
      if (narrative.trendDescription) {
        content += ' ' + narrative.trendDescription;
      }
      if (narrative.peerComparison) {
        content += ' ' + narrative.peerComparison;
      }
      if (narrative.historicalContext) {
        content += ' ' + narrative.historicalContext;
      }

      // Update message with data
      updateMessage(loadingId, {
        content,
        data,
        narrative,
        isLoading: false,
      });

      setLastData(data);
    } catch (error) {
      console.error('Error processing query:', error);

      let errorMessage = 'Sorry, I encountered an error while fetching the data.';

      if (error instanceof Error) {
        if (error.message.includes('No data available')) {
          errorMessage = 'No data available for the requested query. This indicator may not have data for the specified countries or time period. Try a different indicator or time range.';
        } else if (error.message.includes('fetch')) {
          errorMessage = 'Unable to connect to the data source. Please check your internet connection and try again.';
        }
      }

      updateMessage(loadingId, {
        content: '',
        error: errorMessage,
        isLoading: false,
      });
    }

    setIsLoading(false);
  }, [addMessage, updateMessage]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setLastData(null);
  }, []);

  return {
    messages,
    isLoading,
    lastData,
    processQuery,
    clearMessages,
  };
}

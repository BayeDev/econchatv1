import { QueryIntent, Country, Indicator } from './types';
import { COUNTRIES, REGIONAL_CODES, INDICATOR_SYNONYMS, INDICATORS, MULTI_INDICATOR_QUERIES } from './constants';

const currentYear = new Date().getFullYear();

export function interpretQuery(query: string, context?: { countries?: Country[], indicators?: Indicator[] }): QueryIntent {
  const normalizedQuery = query.toLowerCase().trim();

  // Extract countries (use context if none found in current query)
  let countries = extractCountries(normalizedQuery);
  if (countries.length === 0 && context?.countries && context.countries.length > 0) {
    countries = context.countries;
  }

  // Extract indicators (multiple supported)
  const indicators = extractMultipleIndicators(normalizedQuery);

  // Use first indicator for backward compatibility, or use context
  let indicator = indicators.length > 0 ? indicators[0] : null;
  if (!indicator && context?.indicators && context.indicators.length > 0) {
    indicator = context.indicators[0];
  }

  // Extract time period
  const { startYear, endYear } = extractTimePeriod(normalizedQuery);

  // Determine query type
  const queryType = determineQueryType(countries, normalizedQuery);

  // Check for ambiguity
  const { isAmbiguous, clarificationNeeded } = checkAmbiguity(countries, indicator, normalizedQuery);

  return {
    countries,
    indicator,
    indicators: indicators.length > 0 ? indicators : (indicator ? [indicator] : []),
    startYear,
    endYear,
    queryType,
    isAmbiguous,
    clarificationNeeded,
    originalQuery: query,
  };
}

function extractCountries(query: string): Country[] {
  const foundCountries: Country[] = [];
  const queryLower = query.toLowerCase();
  const matchedCodes = new Set<string>();

  // Helper function to check if a name appears as a whole word/phrase in the query
  const matchesWholeWord = (name: string): boolean => {
    // Create a regex that matches the name as a whole word
    // Handle possessives (nigeria's), punctuation, and word boundaries
    const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex = new RegExp(`(^|[^a-z])${escaped}('s)?([^a-z]|$)`, 'i');
    return regex.test(queryLower);
  };

  // First check for regional aggregates
  for (const [name, code] of Object.entries(REGIONAL_CODES)) {
    if (matchesWholeWord(name) && !matchedCodes.has(code)) {
      foundCountries.push({ name: formatName(name), iso3: code });
      matchedCodes.add(code);
    }
  }

  // Then check for individual countries
  // Sort by length descending to match longer names first (e.g., "south africa" before "africa")
  const sortedCountries = Object.entries(COUNTRIES).sort((a, b) => b[0].length - a[0].length);

  for (const [name, code] of sortedCountries) {
    // Check if country name appears as whole word and hasn't been matched already
    if (matchesWholeWord(name) && !matchedCodes.has(code)) {
      foundCountries.push({ name: formatName(name), iso3: code });
      matchedCodes.add(code);
    }
  }

  return foundCountries;
}

function extractIndicator(query: string): Indicator | null {
  const queryLower = query.toLowerCase();

  // Check for "economic snapshot" or similar broad queries
  if (queryLower.includes('snapshot') || queryLower.includes('overview') || queryLower.includes('summary')) {
    // Default to GDP growth for snapshots
    return INDICATORS['NY.GDP.MKTP.KD.ZG'];
  }

  // Sort by length descending to match longer phrases first
  const sortedSynonyms = Object.entries(INDICATOR_SYNONYMS).sort((a, b) => b[0].length - a[0].length);

  for (const [synonym, code] of sortedSynonyms) {
    if (queryLower.includes(synonym)) {
      return INDICATORS[code] || { code, name: synonym, unit: '' };
    }
  }

  return null;
}

function extractMultipleIndicators(query: string): Indicator[] {
  const queryLower = query.toLowerCase();
  const foundIndicators: Indicator[] = [];
  const foundCodes = new Set<string>();

  // First check for multi-indicator query concepts (e.g., "structural transformation")
  for (const [concept, codes] of Object.entries(MULTI_INDICATOR_QUERIES)) {
    if (queryLower.includes(concept)) {
      for (const code of codes) {
        if (!foundCodes.has(code) && INDICATORS[code]) {
          foundIndicators.push(INDICATORS[code]);
          foundCodes.add(code);
        }
      }
      // If we found a multi-indicator concept, return those indicators
      if (foundIndicators.length > 0) {
        return foundIndicators;
      }
    }
  }

  // Sort by length descending to match longer phrases first
  const sortedSynonyms = Object.entries(INDICATOR_SYNONYMS).sort((a, b) => b[0].length - a[0].length);

  // Check for comma-separated or "and"-separated indicators
  // Split query by commas and "and"
  const parts = queryLower.split(/[,]|\band\b/).map(p => p.trim());

  for (const part of parts) {
    for (const [synonym, code] of sortedSynonyms) {
      if (part.includes(synonym) && !foundCodes.has(code)) {
        const indicator = INDICATORS[code];
        if (indicator) {
          foundIndicators.push(indicator);
          foundCodes.add(code);
        }
        break; // Only match first indicator per part
      }
    }
  }

  // If no comma/and separated indicators, try to find any indicators in the whole query
  if (foundIndicators.length === 0) {
    for (const [synonym, code] of sortedSynonyms) {
      if (queryLower.includes(synonym) && !foundCodes.has(code)) {
        const indicator = INDICATORS[code];
        if (indicator) {
          foundIndicators.push(indicator);
          foundCodes.add(code);
        }
      }
    }
  }

  return foundIndicators;
}

function extractTimePeriod(query: string): { startYear: number; endYear: number } {
  const queryLower = query.toLowerCase();

  // Look for explicit year ranges like "2015-2023", "2015 to 2023", "from 2015 to 2023"
  const rangeMatch = query.match(/(\d{4})\s*[-–to]+\s*(\d{4})/i);
  if (rangeMatch) {
    return {
      startYear: parseInt(rangeMatch[1]),
      endYear: parseInt(rangeMatch[2]),
    };
  }

  // Look for "since YYYY"
  const sinceMatch = query.match(/since\s+(\d{4})/i);
  if (sinceMatch) {
    return {
      startYear: parseInt(sinceMatch[1]),
      endYear: currentYear,
    };
  }

  // Look for "last N years"
  const lastYearsMatch = query.match(/last\s+(\d+)\s+years?/i);
  if (lastYearsMatch) {
    const years = parseInt(lastYearsMatch[1]);
    return {
      startYear: currentYear - years,
      endYear: currentYear,
    };
  }

  // Look for "over the past N years"
  const pastYearsMatch = query.match(/(?:over\s+the\s+)?past\s+(\d+)\s+years?/i);
  if (pastYearsMatch) {
    const years = parseInt(pastYearsMatch[1]);
    return {
      startYear: currentYear - years,
      endYear: currentYear,
    };
  }

  // Look for single year mention
  const singleYearMatch = query.match(/\b(19\d{2}|20\d{2})\b/);
  if (singleYearMatch) {
    const year = parseInt(singleYearMatch[1]);
    // If asking about a specific year, show a range around it
    return {
      startYear: year,
      endYear: currentYear,
    };
  }

  // Look for relative time periods
  if (queryLower.includes('recent') || queryLower.includes('lately')) {
    return {
      startYear: currentYear - 5,
      endYear: currentYear,
    };
  }

  // Default: last 10 years
  return {
    startYear: currentYear - 10,
    endYear: currentYear,
  };
}

function determineQueryType(
  countries: Country[],
  query: string
): 'single_country_trend' | 'cross_country_comparison' | 'regional_aggregate' | 'snapshot' {
  const queryLower = query.toLowerCase();

  // Check for snapshot/overview queries
  if (queryLower.includes('snapshot') || queryLower.includes('overview')) {
    return 'snapshot';
  }

  // Check for comparison keywords
  if (queryLower.includes('compare') || queryLower.includes('versus') || queryLower.includes(' vs ')) {
    return 'cross_country_comparison';
  }

  // Check if regional aggregate
  const isRegional = countries.some(c => Object.values(REGIONAL_CODES).includes(c.iso3));
  if (isRegional && countries.length === 1) {
    return 'regional_aggregate';
  }

  // Multiple countries = comparison
  if (countries.length > 1) {
    return 'cross_country_comparison';
  }

  // Single country = trend
  return 'single_country_trend';
}

function checkAmbiguity(
  countries: Country[],
  indicator: Indicator | null,
  query: string
): { isAmbiguous: boolean; clarificationNeeded?: string } {
  // No countries found
  if (countries.length === 0) {
    return {
      isAmbiguous: true,
      clarificationNeeded: 'Which country or region would you like data for?',
    };
  }

  // No indicator found (unless it's a snapshot query)
  if (!indicator && !query.includes('snapshot') && !query.includes('overview')) {
    return {
      isAmbiguous: true,
      clarificationNeeded: 'Which economic indicator are you interested in? (e.g., GDP growth, inflation, unemployment)',
    };
  }

  return { isAmbiguous: false };
}

function formatName(name: string): string {
  return name
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export function getSimilarCountries(query: string): string[] {
  const queryLower = query.toLowerCase();
  const suggestions: string[] = [];

  for (const countryName of Object.keys(COUNTRIES)) {
    // Simple fuzzy match: check if any word starts with query
    const words = countryName.split(' ');
    for (const word of words) {
      if (word.startsWith(queryLower) || queryLower.startsWith(word.slice(0, 3))) {
        suggestions.push(formatName(countryName));
        break;
      }
    }
  }

  return suggestions.slice(0, 5);
}

export function getSimilarIndicators(query: string): Indicator[] {
  const queryLower = query.toLowerCase();
  const suggestions: Indicator[] = [];
  const addedCodes = new Set<string>();

  for (const [synonym, code] of Object.entries(INDICATOR_SYNONYMS)) {
    if (synonym.includes(queryLower) && !addedCodes.has(code)) {
      const indicator = INDICATORS[code];
      if (indicator) {
        suggestions.push(indicator);
        addedCodes.add(code);
      }
    }
  }

  return suggestions.slice(0, 5);
}

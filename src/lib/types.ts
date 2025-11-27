export interface Country {
  name: string;
  iso3: string;
  iso2?: string;
}

export interface Indicator {
  code: string;
  name: string;
  unit: string;
}

export interface DataPoint {
  country: string;
  countryCode: string;
  indicator: string;
  indicatorCode: string;
  year: number;
  value: number | null;
}

export interface QueryIntent {
  countries: Country[];
  indicator: Indicator | null;
  indicators: Indicator[]; // Support for multiple indicators
  startYear: number;
  endYear: number;
  queryType: 'single_country_trend' | 'cross_country_comparison' | 'regional_aggregate' | 'snapshot';
  isAmbiguous: boolean;
  clarificationNeeded?: string;
  originalQuery: string;
  preferredFormat?: VisualizationFormat; // User's preferred visualization format
}

export interface EconomicData {
  data: DataPoint[];
  indicator: Indicator;
  countries: Country[];
  startYear: number;
  endYear: number;
  source: string;
  fetchedAt: Date;
}

export interface NarrativeResponse {
  summary: string;
  trendDescription: string;
  peerComparison?: string;
  historicalContext?: string;
  notableFlags: string[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  data?: EconomicData;
  multipleData?: EconomicData[]; // Support for multiple indicators
  narrative?: NarrativeResponse;
  multipleNarratives?: NarrativeResponse[]; // Support for multiple narratives
  error?: string;
  isLoading?: boolean;
  preferredFormat?: VisualizationFormat; // User's preferred visualization format
}

export interface QuickAction {
  label: string;
  action: string;
  icon?: string;
}

export interface WorldBankResponse {
  page: number;
  pages: number;
  per_page: number;
  total: number;
}

export interface WorldBankDataPoint {
  indicator: {
    id: string;
    value: string;
  };
  country: {
    id: string;
    value: string;
  };
  countryiso3code: string;
  date: string;
  value: number | null;
  decimal: number;
}

export type ChartType = 'line' | 'bar' | 'area';

export type VisualizationFormat = 'chart' | 'table' | 'csv' | 'png';

export interface ChartConfig {
  type: ChartType;
  title: string;
  xAxisLabel: string;
  yAxisLabel: string;
}

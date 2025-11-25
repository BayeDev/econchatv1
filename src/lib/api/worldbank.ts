import { DataPoint, EconomicData, Country, Indicator, WorldBankDataPoint } from '../types';
import { INDICATORS, CITATIONS } from '../constants';

const BASE_URL = 'https://api.worldbank.org/v2';

export async function fetchWorldBankData(
  countryCodes: string[],
  indicatorCode: string,
  startYear: number,
  endYear: number
): Promise<EconomicData> {
  const countryParam = countryCodes.join(';');
  const url = `${BASE_URL}/country/${countryParam}/indicator/${indicatorCode}?format=json&date=${startYear}:${endYear}&per_page=1000`;

  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`World Bank API error: ${response.status} ${response.statusText}`);
  }

  const json = await response.json();

  if (!json || json.length < 2 || !json[1]) {
    throw new Error('No data available for the requested query');
  }

  const rawData: WorldBankDataPoint[] = json[1];
  const indicator = INDICATORS[indicatorCode] || {
    code: indicatorCode,
    name: rawData[0]?.indicator?.value || indicatorCode,
    unit: '',
  };

  const countriesMap = new Map<string, Country>();
  const dataPoints: DataPoint[] = [];

  for (const item of rawData) {
    if (item.value !== null) {
      const country: Country = {
        name: item.country.value,
        iso3: item.countryiso3code,
        iso2: item.country.id,
      };
      countriesMap.set(item.countryiso3code, country);

      dataPoints.push({
        country: item.country.value,
        countryCode: item.countryiso3code,
        indicator: indicator.name,
        indicatorCode: indicatorCode,
        year: parseInt(item.date),
        value: item.value,
      });
    }
  }

  // Sort by year ascending, then by country
  dataPoints.sort((a, b) => {
    if (a.year !== b.year) return a.year - b.year;
    return a.country.localeCompare(b.country);
  });

  return {
    data: dataPoints,
    indicator,
    countries: Array.from(countriesMap.values()),
    startYear,
    endYear,
    source: CITATIONS.worldbank,
    fetchedAt: new Date(),
  };
}

export async function fetchRegionalAverage(
  regionCode: string,
  indicatorCode: string,
  startYear: number,
  endYear: number
): Promise<DataPoint[]> {
  const url = `${BASE_URL}/country/${regionCode}/indicator/${indicatorCode}?format=json&date=${startYear}:${endYear}&per_page=100`;

  const response = await fetch(url);

  if (!response.ok) {
    return [];
  }

  const json = await response.json();

  if (!json || json.length < 2 || !json[1]) {
    return [];
  }

  const rawData: WorldBankDataPoint[] = json[1];
  const indicator = INDICATORS[indicatorCode];

  return rawData
    .filter(item => item.value !== null)
    .map(item => ({
      country: item.country.value,
      countryCode: item.countryiso3code,
      indicator: indicator?.name || indicatorCode,
      indicatorCode,
      year: parseInt(item.date),
      value: item.value,
    }))
    .sort((a, b) => a.year - b.year);
}

export async function searchCountries(query: string): Promise<Country[]> {
  const url = `${BASE_URL}/country?format=json&per_page=300`;

  const response = await fetch(url);
  if (!response.ok) return [];

  const json = await response.json();
  if (!json || json.length < 2) return [];

  const countries = json[1] as Array<{
    id: string;
    iso2Code: string;
    name: string;
    capitalCity: string;
  }>;

  const searchLower = query.toLowerCase();
  return countries
    .filter(c =>
      c.name.toLowerCase().includes(searchLower) ||
      c.id.toLowerCase() === searchLower ||
      c.iso2Code.toLowerCase() === searchLower
    )
    .map(c => ({
      name: c.name,
      iso3: c.id,
      iso2: c.iso2Code,
    }))
    .slice(0, 5);
}

export async function getCountryRegion(countryCode: string): Promise<string | null> {
  const url = `${BASE_URL}/country/${countryCode}?format=json`;

  const response = await fetch(url);
  if (!response.ok) return null;

  const json = await response.json();
  if (!json || json.length < 2 || !json[1] || !json[1][0]) return null;

  const country = json[1][0];
  return country.region?.id || null;
}

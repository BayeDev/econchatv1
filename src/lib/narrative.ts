import { EconomicData, DataPoint, NarrativeResponse } from './types';

export function generateNarrative(
  data: EconomicData,
  regionalData?: DataPoint[]
): NarrativeResponse {
  const { data: dataPoints, indicator, countries } = data;

  if (dataPoints.length === 0) {
    return {
      summary: 'No data available for the requested query.',
      trendDescription: '',
      notableFlags: ['Data not available for the specified period'],
    };
  }

  // Group data by country
  const byCountry = groupByCountry(dataPoints);

  if (countries.length === 1) {
    return generateSingleCountryNarrative(byCountry, indicator.name, indicator.unit, regionalData);
  } else {
    return generateComparisonNarrative(byCountry, indicator.name, indicator.unit);
  }
}

function groupByCountry(dataPoints: DataPoint[]): Map<string, DataPoint[]> {
  const grouped = new Map<string, DataPoint[]>();
  for (const point of dataPoints) {
    const existing = grouped.get(point.country) || [];
    existing.push(point);
    grouped.set(point.country, existing);
  }
  // Sort each country's data by year
  for (const [country, points] of grouped) {
    grouped.set(country, points.sort((a, b) => a.year - b.year));
  }
  return grouped;
}

function generateSingleCountryNarrative(
  byCountry: Map<string, DataPoint[]>,
  indicatorName: string,
  unit: string,
  regionalData?: DataPoint[]
): NarrativeResponse {
  const [countryName, points] = Array.from(byCountry.entries())[0];
  const notableFlags: string[] = [];

  if (points.length === 0) {
    return {
      summary: `No ${indicatorName} data available for ${countryName}.`,
      trendDescription: '',
      notableFlags: ['Data not available'],
    };
  }

  // Get latest and previous values
  const latest = points[points.length - 1];
  const previous = points.length > 1 ? points[points.length - 2] : null;
  const oldest = points[0];

  // Format value based on indicator
  const formattedLatest = formatValue(latest.value, unit);

  // Build summary
  let summary = `${countryName}'s ${indicatorName} was ${formattedLatest} in ${latest.year}`;

  // Add trend description
  let trendDescription = '';
  if (previous && latest.value !== null && previous.value !== null) {
    const change = latest.value - previous.value;
    const percentChange = (change / Math.abs(previous.value)) * 100;
    const direction = change > 0 ? 'increased' : 'decreased';

    if (unit.includes('%')) {
      trendDescription = `${indicatorName} ${direction} by ${Math.abs(change).toFixed(1)} percentage points from ${previous.year} to ${latest.year}.`;
    } else {
      trendDescription = `This represents a ${Math.abs(percentChange).toFixed(1)}% ${direction} from ${previous.year}.`;
    }
    summary += `, ${direction} from ${formatValue(previous.value, unit)} in ${previous.year}`;
  }
  summary += '.';

  // Add historical context
  let historicalContext: string | undefined;
  if (points.length >= 3 && latest.value !== null) {
    const values = points.filter(p => p.value !== null).map(p => p.value as number);
    const max = Math.max(...values);
    const min = Math.min(...values);
    const maxYear = points.find(p => p.value === max)?.year;
    const minYear = points.find(p => p.value === min)?.year;

    if (latest.value === max) {
      historicalContext = `This is the highest level since ${oldest.year}.`;
      notableFlags.push(`Highest ${indicatorName} in the data period`);
    } else if (latest.value === min) {
      historicalContext = `This is the lowest level since ${oldest.year}.`;
      notableFlags.push(`Lowest ${indicatorName} in the data period`);
    } else {
      const avg = values.reduce((a, b) => a + b, 0) / values.length;
      if (latest.value > avg * 1.2) {
        historicalContext = `This is above the period average of ${formatValue(avg, unit)}.`;
      } else if (latest.value < avg * 0.8) {
        historicalContext = `This is below the period average of ${formatValue(avg, unit)}.`;
      }
    }

    // Check for consecutive trends
    const consecutiveTrend = findConsecutiveTrend(points);
    if (consecutiveTrend) {
      notableFlags.push(consecutiveTrend);
    }
  }

  // Add peer comparison if regional data available
  let peerComparison: string | undefined;
  if (regionalData && regionalData.length > 0) {
    const latestRegional = regionalData.find(r => r.year === latest.year);
    if (latestRegional && latestRegional.value !== null && latest.value !== null) {
      const diff = latest.value - latestRegional.value;
      const comparison = diff > 0 ? 'above' : 'below';
      peerComparison = `This is ${comparison} the regional average of ${formatValue(latestRegional.value, unit)}.`;
    }
  }

  // Detect data gaps
  detectDataGaps(points, notableFlags);

  return {
    summary,
    trendDescription,
    peerComparison,
    historicalContext,
    notableFlags,
  };
}

function generateComparisonNarrative(
  byCountry: Map<string, DataPoint[]>,
  indicatorName: string,
  unit: string
): NarrativeResponse {
  const notableFlags: string[] = [];
  const countries = Array.from(byCountry.keys());

  // Get latest values for each country
  const latestValues: { country: string; value: number; year: number }[] = [];

  for (const [country, points] of byCountry) {
    const validPoints = points.filter(p => p.value !== null);
    if (validPoints.length > 0) {
      const latest = validPoints[validPoints.length - 1];
      latestValues.push({
        country,
        value: latest.value as number,
        year: latest.year,
      });
    }
  }

  if (latestValues.length === 0) {
    return {
      summary: `No ${indicatorName} data available for the selected countries.`,
      trendDescription: '',
      notableFlags: ['Data not available'],
    };
  }

  // Sort by value descending
  latestValues.sort((a, b) => b.value - a.value);
  const highest = latestValues[0];
  const lowest = latestValues[latestValues.length - 1];

  // Build summary
  let summary = `Among the selected countries, ${highest.country} had the highest ${indicatorName} at ${formatValue(highest.value, unit)} in ${highest.year}`;

  if (latestValues.length > 1) {
    summary += `, while ${lowest.country} had the lowest at ${formatValue(lowest.value, unit)}`;
  }
  summary += '.';

  // Calculate average
  const avg = latestValues.reduce((sum, v) => sum + v.value, 0) / latestValues.length;

  // Build trend description comparing trajectories
  let trendDescription = '';
  const trends: { country: string; direction: string; magnitude: number }[] = [];

  for (const [country, points] of byCountry) {
    const validPoints = points.filter(p => p.value !== null);
    if (validPoints.length >= 2) {
      const first = validPoints[0].value as number;
      const last = validPoints[validPoints.length - 1].value as number;
      const change = last - first;
      trends.push({
        country,
        direction: change > 0 ? 'increased' : 'decreased',
        magnitude: Math.abs(change),
      });
    }
  }

  if (trends.length > 0) {
    const increasing = trends.filter(t => t.direction === 'increased');
    const decreasing = trends.filter(t => t.direction === 'decreased');

    if (increasing.length > 0 && decreasing.length > 0) {
      const topIncreasing = increasing.sort((a, b) => b.magnitude - a.magnitude)[0];
      const topDecreasing = decreasing.sort((a, b) => b.magnitude - a.magnitude)[0];
      trendDescription = `${topIncreasing.country} showed the largest increase, while ${topDecreasing.country} experienced a decline over the period.`;
    } else if (increasing.length > 0) {
      trendDescription = `All selected countries showed increases in ${indicatorName} over the period.`;
    } else {
      trendDescription = `All selected countries showed decreases in ${indicatorName} over the period.`;
    }
  }

  // Add notable flags
  const gap = highest.value - lowest.value;
  if (gap > avg * 0.5) {
    notableFlags.push(`Significant disparity between countries (${formatValue(gap, unit)} gap)`);
  }

  // Check for convergence/divergence
  const convergenceFlag = checkConvergence(byCountry);
  if (convergenceFlag) {
    notableFlags.push(convergenceFlag);
  }

  return {
    summary,
    trendDescription,
    peerComparison: `The average across selected countries is ${formatValue(avg, unit)}.`,
    notableFlags,
  };
}

function formatValue(value: number | null, unit: string): string {
  if (value === null) return 'N/A';

  if (unit.includes('%')) {
    return `${value.toFixed(1)}%`;
  }

  if (unit.toLowerCase().includes('usd') || unit.toLowerCase().includes('dollar')) {
    if (Math.abs(value) >= 1e12) {
      return `$${(value / 1e12).toFixed(2)} trillion`;
    } else if (Math.abs(value) >= 1e9) {
      return `$${(value / 1e9).toFixed(2)} billion`;
    } else if (Math.abs(value) >= 1e6) {
      return `$${(value / 1e6).toFixed(2)} million`;
    }
    return `$${value.toLocaleString()}`;
  }

  if (unit.toLowerCase().includes('total') || unit.toLowerCase().includes('population')) {
    if (Math.abs(value) >= 1e9) {
      return `${(value / 1e9).toFixed(2)} billion`;
    } else if (Math.abs(value) >= 1e6) {
      return `${(value / 1e6).toFixed(2)} million`;
    }
    return value.toLocaleString();
  }

  if (unit.toLowerCase().includes('year')) {
    return `${value.toFixed(1)} years`;
  }

  if (unit.toLowerCase().includes('index')) {
    return value.toFixed(1);
  }

  return value.toFixed(2);
}

function findConsecutiveTrend(points: DataPoint[]): string | null {
  if (points.length < 3) return null;

  let consecutiveIncreases = 0;
  let consecutiveDecreases = 0;

  for (let i = points.length - 1; i > 0; i--) {
    const current = points[i].value;
    const previous = points[i - 1].value;

    if (current === null || previous === null) break;

    if (current > previous) {
      if (consecutiveDecreases > 0) break;
      consecutiveIncreases++;
    } else if (current < previous) {
      if (consecutiveIncreases > 0) break;
      consecutiveDecreases++;
    } else {
      break;
    }
  }

  if (consecutiveIncreases >= 3) {
    return `${consecutiveIncreases} consecutive years of increase`;
  } else if (consecutiveDecreases >= 3) {
    return `${consecutiveDecreases} consecutive years of decline`;
  }

  return null;
}

function detectDataGaps(points: DataPoint[], flags: string[]): void {
  for (let i = 1; i < points.length; i++) {
    const gap = points[i].year - points[i - 1].year;
    if (gap > 1) {
      flags.push(`Data gap: no values for ${points[i - 1].year + 1}-${points[i].year - 1}`);
    }
  }

  const nullCount = points.filter(p => p.value === null).length;
  if (nullCount > points.length * 0.3) {
    flags.push('Significant missing data in this series');
  }
}

function checkConvergence(byCountry: Map<string, DataPoint[]>): string | null {
  const countries = Array.from(byCountry.entries());
  if (countries.length < 2) return null;

  // Get earliest and latest standard deviations
  const years = new Set<number>();
  for (const [, points] of countries) {
    for (const p of points) {
      if (p.value !== null) years.add(p.year);
    }
  }

  const sortedYears = Array.from(years).sort((a, b) => a - b);
  if (sortedYears.length < 2) return null;

  const firstYear = sortedYears[0];
  const lastYear = sortedYears[sortedYears.length - 1];

  const firstValues: number[] = [];
  const lastValues: number[] = [];

  for (const [, points] of countries) {
    const first = points.find(p => p.year === firstYear && p.value !== null);
    const last = points.find(p => p.year === lastYear && p.value !== null);
    if (first?.value !== undefined && first.value !== null) firstValues.push(first.value);
    if (last?.value !== undefined && last.value !== null) lastValues.push(last.value);
  }

  if (firstValues.length < 2 || lastValues.length < 2) return null;

  const firstStdDev = standardDeviation(firstValues);
  const lastStdDev = standardDeviation(lastValues);

  if (lastStdDev < firstStdDev * 0.7) {
    return 'Countries showing convergence over the period';
  } else if (lastStdDev > firstStdDev * 1.3) {
    return 'Countries showing divergence over the period';
  }

  return null;
}

function standardDeviation(values: number[]): number {
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  const squareDiffs = values.map(v => Math.pow(v - mean, 2));
  return Math.sqrt(squareDiffs.reduce((a, b) => a + b, 0) / values.length);
}

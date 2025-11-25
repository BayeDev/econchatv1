'use client';

import { EconomicData } from '@/lib/types';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface DataChartProps {
  data: EconomicData;
}

const CHART_COLORS = [
  '#58a6ff', // accent blue
  '#3fb950', // green
  '#d29922', // yellow/orange
  '#f85149', // red
  '#a371f7', // purple
  '#79c0ff', // light blue
  '#56d364', // light green
  '#e3b341', // gold
];

export default function DataChart({ data }: DataChartProps) {
  const { data: dataPoints, countries, indicator } = data;

  // Determine chart type based on data
  const isComparison = countries.length > 1;
  const years = [...new Set(dataPoints.map(d => d.year))].sort((a, b) => a - b);

  if (isComparison) {
    // Multi-country comparison - pivot data for chart
    const chartData = years.map(year => {
      const yearData: Record<string, number | string> = { year: year.toString() };
      for (const country of countries) {
        const point = dataPoints.find(d => d.year === year && d.countryCode === country.iso3);
        if (point?.value !== null && point?.value !== undefined) {
          yearData[country.name] = point.value;
        }
      }
      return yearData;
    });

    // Use line chart for time series comparison
    if (years.length > 3) {
      return (
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
            <XAxis
              dataKey="year"
              stroke="#8b949e"
              tick={{ fill: '#8b949e' }}
              axisLine={{ stroke: '#30363d' }}
            />
            <YAxis
              stroke="#8b949e"
              tick={{ fill: '#8b949e' }}
              axisLine={{ stroke: '#30363d' }}
              tickFormatter={(value) => formatYAxisValue(value, indicator.unit)}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#161b22',
                border: '1px solid #30363d',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#f0f6fc' }}
              formatter={(value: number) => [formatValue(value, indicator.unit), '']}
            />
            <Legend wrapperStyle={{ color: '#8b949e' }} />
            {countries.map((country, index) => (
              <Line
                key={country.iso3}
                type="monotone"
                dataKey={country.name}
                stroke={CHART_COLORS[index % CHART_COLORS.length]}
                strokeWidth={2}
                dot={{ fill: CHART_COLORS[index % CHART_COLORS.length], strokeWidth: 0, r: 4 }}
                activeDot={{ r: 6, strokeWidth: 0 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      );
    }

    // Use bar chart for few data points
    return (
      <ResponsiveContainer width="100%" height={350}>
        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
          <XAxis
            dataKey="year"
            stroke="#8b949e"
            tick={{ fill: '#8b949e' }}
            axisLine={{ stroke: '#30363d' }}
          />
          <YAxis
            stroke="#8b949e"
            tick={{ fill: '#8b949e' }}
            axisLine={{ stroke: '#30363d' }}
            tickFormatter={(value) => formatYAxisValue(value, indicator.unit)}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#161b22',
              border: '1px solid #30363d',
              borderRadius: '8px',
            }}
            labelStyle={{ color: '#f0f6fc' }}
            formatter={(value: number) => [formatValue(value, indicator.unit), '']}
          />
          <Legend wrapperStyle={{ color: '#8b949e' }} />
          {countries.map((country, index) => (
            <Bar
              key={country.iso3}
              dataKey={country.name}
              fill={CHART_COLORS[index % CHART_COLORS.length]}
              radius={[4, 4, 0, 0]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    );
  }

  // Single country - line chart
  const chartData = dataPoints
    .filter(d => d.value !== null)
    .map(d => ({
      year: d.year.toString(),
      value: d.value,
    }));

  return (
    <ResponsiveContainer width="100%" height={350}>
      <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
        <XAxis
          dataKey="year"
          stroke="#8b949e"
          tick={{ fill: '#8b949e' }}
          axisLine={{ stroke: '#30363d' }}
        />
        <YAxis
          stroke="#8b949e"
          tick={{ fill: '#8b949e' }}
          axisLine={{ stroke: '#30363d' }}
          tickFormatter={(value) => formatYAxisValue(value, indicator.unit)}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#161b22',
            border: '1px solid #30363d',
            borderRadius: '8px',
          }}
          labelStyle={{ color: '#f0f6fc' }}
          formatter={(value: number) => [formatValue(value, indicator.unit), indicator.name]}
        />
        <Line
          type="monotone"
          dataKey="value"
          stroke={CHART_COLORS[0]}
          strokeWidth={2}
          dot={{ fill: CHART_COLORS[0], strokeWidth: 0, r: 4 }}
          activeDot={{ r: 6, strokeWidth: 0 }}
          name={indicator.name}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

function formatValue(value: number | null, unit: string): string {
  if (value === null) return 'N/A';

  if (unit.includes('%')) {
    return `${value.toFixed(2)}%`;
  }

  if (unit.toLowerCase().includes('usd')) {
    if (Math.abs(value) >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (Math.abs(value) >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (Math.abs(value) >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    return `$${value.toLocaleString()}`;
  }

  if (Math.abs(value) >= 1e9) return `${(value / 1e9).toFixed(2)}B`;
  if (Math.abs(value) >= 1e6) return `${(value / 1e6).toFixed(2)}M`;

  return value.toFixed(2);
}

function formatYAxisValue(value: number, unit: string): string {
  if (unit.includes('%')) {
    return `${value}%`;
  }

  if (Math.abs(value) >= 1e12) return `${(value / 1e12).toFixed(0)}T`;
  if (Math.abs(value) >= 1e9) return `${(value / 1e9).toFixed(0)}B`;
  if (Math.abs(value) >= 1e6) return `${(value / 1e6).toFixed(0)}M`;

  return value.toLocaleString();
}

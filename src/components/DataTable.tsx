'use client';

import { useState, useMemo } from 'react';
import { EconomicData } from '@/lib/types';
import { ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';

interface DataTableProps {
  data: EconomicData;
}

type SortDirection = 'asc' | 'desc' | null;
type SortField = 'year' | 'country' | 'value';

export default function DataTable({ data }: DataTableProps) {
  const [sortField, setSortField] = useState<SortField>('year');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  const sortedData = useMemo(() => {
    if (!sortDirection) return data.data;

    return [...data.data].sort((a, b) => {
      let comparison = 0;

      switch (sortField) {
        case 'year':
          comparison = a.year - b.year;
          break;
        case 'country':
          comparison = a.country.localeCompare(b.country);
          break;
        case 'value':
          const aVal = a.value ?? -Infinity;
          const bVal = b.value ?? -Infinity;
          comparison = aVal - bVal;
          break;
      }

      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [data.data, sortField, sortDirection]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      // Toggle direction
      if (sortDirection === 'asc') {
        setSortDirection('desc');
      } else if (sortDirection === 'desc') {
        setSortDirection(null);
      } else {
        setSortDirection('asc');
      }
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field || !sortDirection) {
      return <ArrowUpDown className="w-4 h-4 opacity-50" />;
    }
    return sortDirection === 'asc' ? (
      <ArrowUp className="w-4 h-4" />
    ) : (
      <ArrowDown className="w-4 h-4" />
    );
  };

  const formatValue = (value: number | null): string => {
    if (value === null) return 'N/A';

    const unit = data.indicator.unit;

    if (unit.includes('%')) {
      return `${value.toFixed(2)}%`;
    }

    if (unit.toLowerCase().includes('usd')) {
      if (Math.abs(value) >= 1e12) return `$${(value / 1e12).toFixed(2)} trillion`;
      if (Math.abs(value) >= 1e9) return `$${(value / 1e9).toFixed(2)} billion`;
      if (Math.abs(value) >= 1e6) return `$${(value / 1e6).toFixed(2)} million`;
      return `$${value.toLocaleString()}`;
    }

    if (Math.abs(value) >= 1e9) return `${(value / 1e9).toFixed(2)} billion`;
    if (Math.abs(value) >= 1e6) return `${(value / 1e6).toFixed(2)} million`;

    return value.toFixed(2);
  };

  // Check if we have multiple countries to show country column
  const showCountryColumn = data.countries.length > 1;

  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="data-table">
        <thead>
          <tr>
            {showCountryColumn && (
              <th
                onClick={() => handleSort('country')}
                className="cursor-pointer hover:bg-surface select-none"
              >
                <div className="flex items-center gap-2">
                  Country
                  <SortIcon field="country" />
                </div>
              </th>
            )}
            <th
              onClick={() => handleSort('year')}
              className="cursor-pointer hover:bg-surface select-none"
            >
              <div className="flex items-center gap-2">
                Year
                <SortIcon field="year" />
              </div>
            </th>
            <th
              onClick={() => handleSort('value')}
              className="cursor-pointer hover:bg-surface select-none"
            >
              <div className="flex items-center gap-2">
                {data.indicator.name}
                <SortIcon field="value" />
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          {sortedData.map((row, index) => (
            <tr key={`${row.countryCode}-${row.year}-${index}`}>
              {showCountryColumn && <td className="font-medium">{row.country}</td>}
              <td>{row.year}</td>
              <td className={row.value === null ? 'text-text-secondary italic' : ''}>
                {formatValue(row.value)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

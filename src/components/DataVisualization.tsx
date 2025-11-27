'use client';

import { useState, useRef, useEffect } from 'react';
import { EconomicData, NarrativeResponse, DataPoint, VisualizationFormat } from '@/lib/types';
import DataChart from './DataChart';
import DataTable from './DataTable';
import { Download, Image, FileSpreadsheet, TrendingUp, TrendingDown, AlertTriangle, BarChart2, Table } from 'lucide-react';

interface DataVisualizationProps {
  data: EconomicData;
  narrative: NarrativeResponse;
  preferredFormat?: VisualizationFormat;
}

export default function DataVisualization({ data, narrative, preferredFormat }: DataVisualizationProps) {
  // Set initial tab based on preferredFormat (table/chart only, csv/png trigger exports)
  const getInitialTab = (): 'chart' | 'table' => {
    if (preferredFormat === 'table') return 'table';
    return 'chart';
  };

  const [activeTab, setActiveTab] = useState<'chart' | 'table'>(getInitialTab());
  const chartRef = useRef<HTMLDivElement>(null);
  const hasAutoExported = useRef(false);

  const exportCSV = () => {
    const headers = ['Country', 'Year', data.indicator.name, 'Unit'];
    const rows = data.data.map(d => [
      d.country,
      d.year.toString(),
      d.value?.toString() || 'N/A',
      data.indicator.unit,
    ]);

    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `econchat_${data.indicator.code}_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportPNG = async () => {
    if (!chartRef.current) return;

    try {
      const html2canvas = (await import('html2canvas')).default;
      const canvas = await html2canvas(chartRef.current, {
        backgroundColor: '#161b22',
        scale: 2,
      });
      const url = canvas.toDataURL('image/png');
      const a = document.createElement('a');
      a.href = url;
      a.download = `econchat_${data.indicator.code}_${Date.now()}.png`;
      a.click();
    } catch (error) {
      console.error('Failed to export PNG:', error);
    }
  };

  // Auto-export for CSV/PNG formats when requested
  useEffect(() => {
    if (hasAutoExported.current) return;

    if (preferredFormat === 'csv') {
      // Small delay to ensure component is fully rendered
      const timer = setTimeout(() => {
        exportCSV();
        hasAutoExported.current = true;
      }, 100);
      return () => clearTimeout(timer);
    }

    if (preferredFormat === 'png') {
      // Longer delay for PNG to ensure chart is fully rendered
      const timer = setTimeout(() => {
        exportPNG();
        hasAutoExported.current = true;
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [preferredFormat]);

  return (
    <div className="card space-y-4">
      {/* Narrative summary */}
      <div className="space-y-3">
        <h3 className="text-lg font-semibold text-text-primary flex items-center gap-2">
          {data.indicator.name}
          <span className="text-sm font-normal text-text-secondary">
            ({data.indicator.unit})
          </span>
        </h3>

        <div className="space-y-2 text-text-secondary">
          <p>{narrative.summary}</p>
          {narrative.trendDescription && <p>{narrative.trendDescription}</p>}
          {narrative.peerComparison && <p>{narrative.peerComparison}</p>}
          {narrative.historicalContext && <p className="text-text-secondary/80">{narrative.historicalContext}</p>}
        </div>

        {/* Notable flags */}
        {narrative.notableFlags.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {narrative.notableFlags.map((flag, index) => (
              <span
                key={index}
                className="inline-flex items-center gap-1 px-2 py-1 bg-warning/10 text-warning text-xs rounded-full"
              >
                <AlertTriangle className="w-3 h-3" />
                {flag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Tab selector */}
      <div className="flex items-center justify-between border-b border-border pb-2">
        <div className="flex gap-1">
          <button
            onClick={() => setActiveTab('chart')}
            className={`btn btn-ghost text-sm ${activeTab === 'chart' ? 'bg-surface-light text-text-primary' : ''}`}
          >
            <BarChart2 className="w-4 h-4" />
            Chart
          </button>
          <button
            onClick={() => setActiveTab('table')}
            className={`btn btn-ghost text-sm ${activeTab === 'table' ? 'bg-surface-light text-text-primary' : ''}`}
          >
            <Table className="w-4 h-4" />
            Table
          </button>
        </div>

        <div className="flex gap-1">
          <button onClick={exportCSV} className="btn btn-ghost text-sm" title="Export CSV">
            <FileSpreadsheet className="w-4 h-4" />
            CSV
          </button>
          <button onClick={exportPNG} className="btn btn-ghost text-sm" title="Export PNG">
            <Image className="w-4 h-4" />
            PNG
          </button>
        </div>
      </div>

      {/* Content */}
      <div ref={chartRef} className="min-h-[300px]">
        {activeTab === 'chart' ? (
          <DataChart data={data} />
        ) : (
          <DataTable data={data} />
        )}
      </div>

      {/* Source citation */}
      <div className="text-xs text-text-secondary border-t border-border pt-3">
        {data.source}
      </div>
    </div>
  );
}

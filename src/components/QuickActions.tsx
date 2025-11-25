'use client';

import { EconomicData } from '@/lib/types';
import { Plus, Calendar, BarChart2, Percent } from 'lucide-react';

interface QuickActionsProps {
  currentData: EconomicData | null;
  onAction: (action: string) => void;
}

export default function QuickActions({ currentData, onAction }: QuickActionsProps) {
  if (!currentData) return null;

  const actions = [
    {
      label: 'Add country',
      action: `Compare ${currentData.countries[0]?.name || 'this country'} with another country`,
      icon: Plus,
    },
    {
      label: 'Extend time range',
      action: `Show ${currentData.indicator.name} from ${currentData.startYear - 5} to ${currentData.endYear}`,
      icon: Calendar,
    },
    {
      label: 'Add indicator',
      action: `Also show inflation for ${currentData.countries.map(c => c.name).join(', ')}`,
      icon: BarChart2,
    },
    {
      label: 'Show % change',
      action: `Show year-over-year percent change for ${currentData.indicator.name}`,
      icon: Percent,
    },
  ];

  return (
    <div className="flex flex-wrap gap-2">
      {actions.map((action, index) => {
        const Icon = action.icon;
        return (
          <button
            key={index}
            onClick={() => onAction(action.action)}
            className="btn btn-ghost text-sm"
          >
            <Icon className="w-4 h-4" />
            {action.label}
          </button>
        );
      })}
    </div>
  );
}

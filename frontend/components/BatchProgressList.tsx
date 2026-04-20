'use client';

import { useMemo } from 'react';
import { Loader2, CheckCircle2, Clock, Search, Sparkles, AlertCircle } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { cn } from '@/lib/cn';
import { AnalysisResult, WineSKUInput } from '@/lib/types';

interface BatchProgressListProps {
  wines: WineSKUInput[];
  results: AnalysisResult[];
  completed: number;
  total: number;
}

type ItemStatus = 'pending' | 'searching' | 'analyzing' | 'completed' | 'error';

interface ItemState {
  input: WineSKUInput;
  result?: AnalysisResult;
  status: ItemStatus;
  index: number;
}

export function BatchProgressList({ wines, results, completed, total }: BatchProgressListProps) {
  const items = useMemo<ItemState[]>(() => {
    return wines.map((input, index) => {
      const result = results.find(
        (r) => r.input.wine_name === input.wine_name && r.input.vintage === input.vintage
      );

      let status: ItemStatus = 'pending';
      if (result) {
        status = 'completed';
      } else if (index < completed) {
        // Should have result but doesn't - likely error
        status = 'error';
      } else if (index === completed) {
        // Currently being processed
        status = 'searching';
      }

      return { input, result, status, index };
    });
  }, [wines, results, completed]);

  const pct = total > 0 ? (completed / total) * 100 : 0;

  return (
    <Card className="overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-border bg-bg-subtle">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-fg">Processing {total} wines</h3>
            <p className="text-xs text-fg-muted mt-0.5">
              {completed} completed · {total - completed} remaining
            </p>
          </div>
          <div className="text-right">
            <span className="text-2xl font-semibold tabular-nums text-fg">{Math.round(pct)}%</span>
          </div>
        </div>
        <div className="mt-3 h-1.5 bg-bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-primary transition-all duration-500 ease-out"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* List */}
      <div className="max-h-[400px] overflow-y-auto">
        <table className="w-full">
          <thead className="sticky top-0 bg-surface z-10">
            <tr className="text-[10px] font-semibold uppercase tracking-wider text-fg-subtle border-b border-border">
              <th className="text-left py-2 pl-4 pr-2 w-10">#</th>
              <th className="text-left py-2 px-2">Wine</th>
              <th className="text-left py-2 px-2 w-24">Status</th>
              <th className="text-right py-2 px-2 w-20">Result</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {items.map((item) => (
              <ProgressRow key={item.index} item={item} />
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function ProgressRow({ item }: { item: ItemState }) {
  const { input, result, status } = item;

  const statusConfig: Record<ItemStatus, { icon: typeof Clock; label: string; color: string; bg: string; animate?: boolean }> = {
    pending: {
      icon: Clock,
      label: 'Pending',
      color: 'text-fg-subtle',
      bg: 'bg-bg-subtle',
    },
    searching: {
      icon: Search,
      label: 'Searching',
      color: 'text-primary',
      bg: 'bg-primary/10',
      animate: true,
    },
    analyzing: {
      icon: Sparkles,
      label: 'Analyzing',
      color: 'text-warning',
      bg: 'bg-warning/10',
      animate: true,
    },
    completed: {
      icon: CheckCircle2,
      label: 'Done',
      color: 'text-success',
      bg: 'bg-success/10',
    },
    error: {
      icon: AlertCircle,
      label: 'Error',
      color: 'text-danger',
      bg: 'bg-danger/10',
    },
  };

  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <tr className={cn('transition-colors', status === 'searching' && 'bg-primary/5')}>
      <td className="py-2.5 pl-4 pr-2 text-xs font-mono text-fg-subtle tabular-nums">
        {String(item.index + 1).padStart(2, '0')}
      </td>
      <td className="py-2.5 px-2">
        <div className="text-sm font-medium text-fg leading-snug line-clamp-1">
          {input.wine_name}
        </div>
        {input.vintage && (
          <div className="text-xs text-fg-muted">{input.vintage}</div>
        )}
      </td>
      <td className="py-2.5 px-2">
        <span
          className={cn(
            'inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium',
            config.bg,
            config.color
          )}
        >
          <Icon className={cn('h-3.5 w-3.5', config.animate && 'animate-spin')} />
          {config.label}
        </span>
      </td>
      <td className="py-2.5 px-2 text-right">
        {result ? (
          <VerdictMini verdict={result.verdict} confidence={result.confidence} />
        ) : (
          <span className="text-xs text-fg-subtle">—</span>
        )}
      </td>
    </tr>
  );
}

function VerdictMini({
  verdict,
  confidence,
}: {
  verdict: AnalysisResult['verdict'];
  confidence: number;
}) {
  const colors = {
    PASS: 'text-success bg-success/10',
    REVIEW: 'text-warning bg-warning/10',
    FAIL: 'text-danger bg-danger/10',
    NO_IMAGE: 'text-fg-subtle bg-bg-muted',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium',
        colors[verdict]
      )}
    >
      {verdict}
      <span className="tabular-nums opacity-70">{confidence.toFixed(0)}%</span>
    </span>
  );
}

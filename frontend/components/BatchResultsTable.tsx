'use client';

import { useMemo, useState } from 'react';
import { ExternalLink, ImageOff, ChevronRight } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { VerdictBadge } from '@/components/ui/Badge';
import { cn } from '@/lib/cn';
import { AnalysisResult } from '@/lib/types';

type Filter = 'all' | 'PASS' | 'REVIEW' | 'FAIL' | 'NO_IMAGE';

export function BatchResultsTable({ results }: { results: AnalysisResult[] }) {
  const [filter, setFilter] = useState<Filter>('all');
  const [expanded, setExpanded] = useState<number | null>(null);

  const counts = useMemo(() => {
    const c = { PASS: 0, REVIEW: 0, FAIL: 0, NO_IMAGE: 0 };
    results.forEach((r) => {
      c[r.verdict] = (c[r.verdict] || 0) + 1;
    });
    return c;
  }, [results]);

  const verified = counts.PASS + counts.REVIEW;
  const accuracy = results.length > 0 ? (verified / results.length) * 100 : 0;
  const targetMet = accuracy >= 90;

  const filtered = useMemo(
    () => (filter === 'all' ? results : results.filter((r) => r.verdict === filter)),
    [results, filter]
  );

  return (
    <Card className="overflow-hidden">
      {/* Summary header */}
      <div className="p-5 border-b border-border bg-bg-subtle">
        <div className="flex items-end justify-between gap-6 flex-wrap mb-4">
          <div>
            <h3 className="text-sm font-semibold text-fg mb-1">
              Batch results
            </h3>
            <p className="text-xs text-fg-muted">
              {results.length} wine{results.length === 1 ? '' : 's'} analyzed ·{' '}
              <span
                className={cn(
                  'font-medium',
                  targetMet ? 'text-success' : 'text-warning'
                )}
              >
                {accuracy.toFixed(0)}% verified
              </span>{' '}
              {targetMet ? '· target met' : `· ${(90 - accuracy).toFixed(0)}% to target`}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <FilterChip
              label="All"
              count={results.length}
              active={filter === 'all'}
              onClick={() => setFilter('all')}
            />
            <FilterChip
              label="Pass"
              count={counts.PASS}
              active={filter === 'PASS'}
              onClick={() => setFilter('PASS')}
              tone="success"
            />
            <FilterChip
              label="Review"
              count={counts.REVIEW}
              active={filter === 'REVIEW'}
              onClick={() => setFilter('REVIEW')}
              tone="warning"
            />
            <FilterChip
              label="Fail"
              count={counts.FAIL}
              active={filter === 'FAIL'}
              onClick={() => setFilter('FAIL')}
              tone="danger"
            />
            <FilterChip
              label="No image"
              count={counts.NO_IMAGE}
              active={filter === 'NO_IMAGE'}
              onClick={() => setFilter('NO_IMAGE')}
            />
          </div>
        </div>

        {/* Accuracy bar */}
        <div className="space-y-1.5">
          <div className="h-1.5 bg-bg-muted rounded-full overflow-hidden flex">
            {results.length > 0 && (
              <>
                <div
                  className="bg-success transition-all"
                  style={{ width: `${(counts.PASS / results.length) * 100}%` }}
                />
                <div
                  className="bg-warning transition-all"
                  style={{ width: `${(counts.REVIEW / results.length) * 100}%` }}
                />
                <div
                  className="bg-danger transition-all"
                  style={{ width: `${(counts.FAIL / results.length) * 100}%` }}
                />
                <div
                  className="bg-fg-subtle/30 transition-all"
                  style={{ width: `${(counts.NO_IMAGE / results.length) * 100}%` }}
                />
              </>
            )}
          </div>
          <div className="flex items-center gap-4 text-[11px] text-fg-subtle">
            <span className="text-fg-muted">90% target</span>
            <div className="flex-1 relative">
              <div className="absolute top-[-7px] h-3 w-px bg-fg-muted/40" style={{ left: '90%' }} />
            </div>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="text-[10px] font-semibold uppercase tracking-wider text-fg-subtle border-b border-border">
              <th className="text-left py-3 pl-5 pr-2 w-10">#</th>
              <th className="text-left py-3 px-2">Wine</th>
              <th className="text-left py-3 px-2 w-28">Vintage</th>
              <th className="text-left py-3 px-2 w-32">Verdict</th>
              <th className="text-right py-3 px-2 w-28">Confidence</th>
              <th className="text-left py-3 px-2 w-20">Image</th>
              <th className="w-10 pr-5"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {filtered.length === 0 && (
              <tr>
                <td colSpan={7} className="text-center py-12 text-fg-muted text-sm">
                  No wines match this filter.
                </td>
              </tr>
            )}
            {filtered.map((r, i) => {
              const isOpen = expanded === i;
              const confColor =
                r.confidence >= 50
                  ? 'text-success'
                  : r.confidence >= 25
                  ? 'text-warning'
                  : 'text-fg-muted';
              return (
                <>
                  <tr
                    key={i}
                    className="hover:bg-bg-subtle/60 transition-colors cursor-pointer"
                    onClick={() => setExpanded(isOpen ? null : i)}
                  >
                    <td className="py-3 pl-5 pr-2 text-xs font-mono text-fg-subtle tabular-nums">
                      {String(i + 1).padStart(2, '0')}
                    </td>
                    <td className="py-3 px-2">
                      <div className="text-sm font-medium text-fg leading-snug line-clamp-1">
                        {r.input.wine_name}
                      </div>
                      {r.parsed_sku.producer && (
                        <div className="text-xs text-fg-muted mt-0.5">
                          {r.parsed_sku.producer}
                          {r.parsed_sku.appellation && ` · ${r.parsed_sku.appellation}`}
                        </div>
                      )}
                    </td>
                    <td className="py-3 px-2 text-sm text-fg-muted tabular-nums">
                      {r.input.vintage || '—'}
                    </td>
                    <td className="py-3 px-2">
                      <VerdictBadge verdict={r.verdict} />
                    </td>
                    <td className="py-3 px-2 text-right">
                      <span className={cn('text-sm font-semibold tabular-nums', confColor)}>
                        {r.confidence.toFixed(1)}
                      </span>
                      <span className="text-[10px] text-fg-subtle ml-1">/100</span>
                    </td>
                    <td className="py-3 px-2">
                      {r.selected_image_url ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={r.selected_image_url}
                          alt=""
                          className="h-10 w-10 object-contain rounded ring-1 ring-border bg-white"
                        />
                      ) : (
                        <div className="h-10 w-10 rounded bg-bg-muted ring-1 ring-border flex items-center justify-center">
                          <ImageOff className="h-4 w-4 text-fg-subtle" />
                        </div>
                      )}
                    </td>
                    <td className="pr-5">
                      <ChevronRight
                        className={cn(
                          'h-4 w-4 text-fg-subtle transition-transform',
                          isOpen && 'rotate-90'
                        )}
                      />
                    </td>
                  </tr>
                  {isOpen && (
                    <tr key={`${i}-detail`} className="bg-bg-subtle/40">
                      <td colSpan={7} className="px-5 py-4">
                        <ExpandedRow result={r} />
                      </td>
                    </tr>
                  )}
                </>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function FilterChip({
  label,
  count,
  active,
  onClick,
  tone,
}: {
  label: string;
  count: number;
  active: boolean;
  onClick: () => void;
  tone?: 'success' | 'warning' | 'danger';
}) {
  const dotColor =
    tone === 'success'
      ? 'bg-success'
      : tone === 'warning'
      ? 'bg-warning'
      : tone === 'danger'
      ? 'bg-danger'
      : 'bg-fg-subtle';
  return (
    <button
      onClick={onClick}
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium ring-1 transition-all',
        active
          ? 'bg-fg text-bg ring-fg shadow-subtle'
          : 'bg-surface text-fg-muted ring-border hover:ring-border-strong hover:text-fg'
      )}
    >
      {tone && <span className={cn('h-1.5 w-1.5 rounded-full', dotColor)} />}
      {label}
      <span className={cn('text-[10px] tabular-nums', active ? 'opacity-80' : 'text-fg-subtle')}>
        {count}
      </span>
    </button>
  );
}

function ExpandedRow({ result }: { result: AnalysisResult }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="md:col-span-2">
        <div className="text-[10px] font-semibold uppercase tracking-wider text-fg-subtle mb-1.5">
          Reasoning
        </div>
        <p className="text-sm text-fg-muted leading-relaxed">{result.reason}</p>

        {result.top_candidates.length > 0 && (
          <div className="mt-4">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-fg-subtle mb-2">
              Top candidates
            </div>
            <div className="flex gap-2 flex-wrap">
              {result.top_candidates.slice(0, 5).map((c, i) => (
                <a
                  key={i}
                  href={c.image_url}
                  target="_blank"
                  rel="noreferrer"
                  className="relative group h-16 w-16 rounded-md ring-1 ring-border overflow-hidden bg-white hover:ring-primary/40"
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={c.image_url}
                    alt=""
                    className="w-full h-full object-contain p-1"
                  />
                  <div className="absolute bottom-0 inset-x-0 bg-black/70 text-white text-[9px] px-1 text-center font-mono">
                    {c.total_score.toFixed(0)}
                  </div>
                </a>
              ))}
            </div>
          </div>
        )}
      </div>

      <div>
        <div className="text-[10px] font-semibold uppercase tracking-wider text-fg-subtle mb-1.5">
          Parsed
        </div>
        <dl className="space-y-1 text-sm">
          {[
            ['Producer', result.parsed_sku.producer],
            ['Appellation', result.parsed_sku.appellation],
            ['Vineyard', result.parsed_sku.vineyard],
            ['Classification', result.parsed_sku.classification],
          ].map(([k, v]) => (
            <div key={k} className="flex justify-between gap-2">
              <dt className="text-fg-subtle">{k}</dt>
              <dd className="text-fg text-right truncate">
                {v || <span className="text-fg-subtle italic">—</span>}
              </dd>
            </div>
          ))}
        </dl>

        {result.selected_image_url && (
          <a
            href={result.selected_image_url}
            target="_blank"
            rel="noreferrer"
            className="mt-3 inline-flex items-center gap-1 text-xs text-primary hover:underline"
          >
            <ExternalLink className="h-3 w-3" /> View image source
          </a>
        )}
      </div>
    </div>
  );
}

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Search, ChevronLeft, ChevronRight, ImageOff } from 'lucide-react';
import { PageHeader } from '@/components/PageHeader';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { VerdictBadge } from '@/components/ui/Badge';
import { listResults } from '@/lib/api';
import { RunSummary } from '@/lib/types';

export default function ResultsPage() {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const pageSize = 20;

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    listResults(page, pageSize, undefined, search || undefined)
      .then((r) => {
        if (cancelled) return;
        setRuns(r.runs);
        setTotal(r.total);
        setError(null);
      })
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [page, search]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div>
      <PageHeader
        eyebrow="History"
        title="Past analyses"
        description="Every run is persisted to SQLite. Filter, search, and dive into individual results."
      />

      <Card className="overflow-hidden">
        <div className="p-4 border-b border-border flex items-center gap-3">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-fg-subtle" />
            <Input
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              placeholder="Search by wine name…"
              className="pl-9"
            />
          </div>
          <span className="text-xs text-fg-muted ml-auto">
            {total} run{total === 1 ? '' : 's'}
          </span>
        </div>

        {error && (
          <div className="p-4 text-sm text-danger bg-danger-soft">{error}</div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-[10px] font-semibold uppercase tracking-wider text-fg-subtle border-b border-border">
                <th className="text-left py-3 px-5">Wine</th>
                <th className="text-left py-3 px-2 w-24">Vintage</th>
                <th className="text-left py-3 px-2 w-32">Verdict</th>
                <th className="text-right py-3 px-2 w-28">Confidence</th>
                <th className="text-left py-3 px-2 w-20">Image</th>
                <th className="text-left py-3 px-5 w-44">When</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {loading && (
                <tr>
                  <td colSpan={6} className="text-center py-12 text-fg-muted text-sm">
                    Loading…
                  </td>
                </tr>
              )}
              {!loading && runs.length === 0 && (
                <tr>
                  <td colSpan={6} className="text-center py-16 text-fg-muted text-sm">
                    No past runs found. Try analyzing a wine first.
                  </td>
                </tr>
              )}
              {!loading &&
                runs.map((r) => (
                  <tr
                    key={r.run_id}
                    className="hover:bg-bg-subtle/60 transition-colors"
                  >
                    <td className="py-3 px-5">
                      <Link
                        href={`/results/${r.run_id}`}
                        className="text-sm font-medium text-fg hover:text-primary line-clamp-1"
                      >
                        {r.wine_name}
                      </Link>
                    </td>
                    <td className="py-3 px-2 text-sm text-fg-muted">
                      {r.vintage || '—'}
                    </td>
                    <td className="py-3 px-2">
                      <VerdictBadge verdict={r.verdict} />
                    </td>
                    <td className="py-3 px-2 text-right text-sm tabular-nums text-fg">
                      {r.confidence.toFixed(1)}
                    </td>
                    <td className="py-3 px-2">
                      <div className="h-9 w-9 rounded ring-1 ring-border bg-bg-muted flex items-center justify-center">
                        {r.has_image ? (
                          <span className="h-2 w-2 rounded-full bg-success" />
                        ) : (
                          <ImageOff className="h-3.5 w-3.5 text-fg-subtle" />
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-5 text-xs text-fg-muted tabular-nums">
                      {new Date(r.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>

        {totalPages > 1 && (
          <div className="p-4 border-t border-border flex items-center justify-between text-sm">
            <span className="text-fg-muted">
              Page {page} of {totalPages}
            </span>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
              >
                <ChevronLeft className="h-3.5 w-3.5" />
                Prev
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={page === totalPages}
                onClick={() => setPage(page + 1)}
              >
                Next
                <ChevronRight className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

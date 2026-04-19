'use client';

import { ExternalLink, Image as ImageIcon, AlertTriangle, CheckCircle2, Sparkles } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { VerdictBadge } from '@/components/ui/Badge';
import { cn } from '@/lib/cn';
import { AnalysisResult } from '@/lib/types';

export function AnalysisResultPanel({ data }: { data: AnalysisResult }) {
  const { parsed_sku, selected_image_url, confidence, verdict, reason, top_candidates } = data;

  const confColor =
    confidence >= 50 ? 'text-success' : confidence >= 25 ? 'text-warning' : 'text-fg-muted';

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Verdict + image hero */}
      <Card className="overflow-hidden">
        <div className="grid grid-cols-1 md:grid-cols-[280px_1fr]">
          <div className="bg-bg-muted border-b md:border-b-0 md:border-r border-border flex items-center justify-center aspect-square md:aspect-auto md:min-h-[260px] relative">
            {selected_image_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={selected_image_url}
                alt={data.input.wine_name}
                className="max-h-full max-w-full object-contain p-6"
              />
            ) : (
              <div className="flex flex-col items-center gap-2 text-fg-subtle">
                <ImageIcon className="h-8 w-8" strokeWidth={1.5} />
                <span className="text-xs font-medium">No verified image</span>
              </div>
            )}
          </div>

          <div className="p-6 flex flex-col">
            <div className="flex items-center gap-2 mb-3">
              <VerdictBadge verdict={verdict} />
              <span className="text-xs text-fg-subtle font-mono">
                {data.analyzer_mode}
              </span>
            </div>

            <h3 className="text-lg font-semibold tracking-tight text-fg leading-snug mb-1">
              {data.input.wine_name}
            </h3>
            <div className="text-sm text-fg-muted mb-4">
              {[data.input.vintage, data.input.region].filter(Boolean).join(' · ')}
            </div>

            <div className="grid grid-cols-2 gap-3 mb-4">
              <Stat label="Confidence" value={`${confidence.toFixed(1)}`} suffix="/100" valueClass={confColor} />
              <Stat
                label="Candidates"
                value={String(top_candidates.length)}
                suffix="evaluated"
              />
            </div>

            {selected_image_url && (
              <a
                href={selected_image_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 text-xs text-primary font-medium hover:underline mb-3 truncate"
              >
                <ExternalLink className="h-3 w-3 shrink-0" />
                <span className="truncate">{selected_image_url}</span>
              </a>
            )}

            <div className="mt-auto pt-3 border-t border-border">
              <div className="text-xs text-fg-subtle uppercase tracking-wider font-medium mb-1.5">
                Reasoning
              </div>
              <p className="text-sm text-fg-muted leading-relaxed">{reason}</p>
            </div>
          </div>
        </div>
      </Card>

      {/* Parsed identity */}
      <Card className="p-5">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="h-4 w-4 text-primary" />
          <h4 className="text-sm font-semibold">Parsed identity</h4>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-3">
          <Field label="Producer" value={parsed_sku.producer} />
          <Field label="Appellation" value={parsed_sku.appellation} />
          <Field label="Vineyard" value={parsed_sku.vineyard} />
          <Field label="Classification" value={parsed_sku.classification} />
          <Field label="Cuvée" value={parsed_sku.cuvee} />
          <Field label="Vintage" value={parsed_sku.vintage} />
          <Field label="Format" value={parsed_sku.format_ml ? `${parsed_sku.format_ml}ml` : undefined} />
          <Field label="Region" value={parsed_sku.region} />
        </div>
      </Card>

      {/* Candidate strip */}
      {top_candidates.length > 0 && (
        <Card className="p-5">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-semibold">Top candidates ({top_candidates.length})</h4>
            <span className="text-xs text-fg-subtle">Highest score → lowest</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
            {top_candidates.slice(0, 5).map((c, i) => (
              <a
                key={i}
                href={c.image_url}
                target="_blank"
                rel="noreferrer"
                className="group relative aspect-[3/4] bg-bg-muted rounded-lg overflow-hidden ring-1 ring-border hover:ring-primary/40 hover:shadow-card transition-all"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={c.image_url}
                  alt={`Candidate ${i + 1}`}
                  className="w-full h-full object-contain p-2"
                />
                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 to-transparent p-2">
                  <div className="flex items-center justify-between text-[10px] font-medium text-white">
                    <span>#{i + 1}</span>
                    <span className="font-mono">{c.total_score.toFixed(1)}</span>
                  </div>
                </div>
              </a>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  suffix,
  valueClass,
}: {
  label: string;
  value: string;
  suffix?: string;
  valueClass?: string;
}) {
  return (
    <div className="rounded-lg bg-bg-subtle ring-1 ring-border p-3">
      <div className="text-[10px] font-medium uppercase tracking-wider text-fg-muted mb-1">
        {label}
      </div>
      <div className="flex items-baseline gap-1">
        <span className={cn('text-xl font-semibold tabular-nums', valueClass ?? 'text-fg')}>
          {value}
        </span>
        {suffix && <span className="text-xs text-fg-subtle">{suffix}</span>}
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <div className="text-[10px] font-medium uppercase tracking-wider text-fg-subtle mb-0.5">
        {label}
      </div>
      <div className="text-sm text-fg truncate">
        {value || <span className="text-fg-subtle italic">—</span>}
      </div>
    </div>
  );
}

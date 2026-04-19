'use client';

import { useState } from 'react';
import { Sparkles, Loader2 } from 'lucide-react';
import { PageHeader } from '@/components/PageHeader';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input, Select, Label } from '@/components/ui/Input';
import { AnalysisResultPanel } from '@/components/AnalysisResultPanel';
import { analyzeWine } from '@/lib/api';
import { AnalysisResult } from '@/lib/types';

const PRESETS = [
  { name: "Domaine Arlaud Morey-St-Denis 'Monts Luisants' 1er Cru", vintage: '2019', region: 'Burgundy' },
  { name: 'Château Fonroque Saint-Émilion Grand Cru Classé', vintage: '2016', region: 'Bordeaux' },
  { name: "Eric Rodez Cuvée des Crayères Blanc de Noirs", vintage: 'NV', region: 'Champagne' },
];

export default function AnalyzePage() {
  const [wineName, setWineName] = useState('');
  const [vintage, setVintage] = useState('');
  const [region, setRegion] = useState('');
  const [mode, setMode] = useState<'hybrid_fast' | 'hybrid_strict'>('hybrid_fast');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!wineName.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const r = await analyzeWine({
        wine_name: wineName.trim(),
        vintage: vintage || undefined,
        region: region || undefined,
        analyzer_mode: mode,
      });
      setResult(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const loadPreset = (p: (typeof PRESETS)[number]) => {
    setWineName(p.name);
    setVintage(p.vintage);
    setRegion(p.region);
  };

  return (
    <div>
      <PageHeader
        eyebrow="Single SKU"
        title="Analyze a wine"
        description="Enter the SKU details. The pipeline searches, screens, OCRs and verifies — typically 20-40 seconds per wine."
      />

      <div className="grid grid-cols-1 lg:grid-cols-[380px_1fr] gap-6">
        {/* Form */}
        <div className="space-y-4">
          <Card className="p-5">
            <form onSubmit={handleAnalyze} className="space-y-4">
              <div>
                <Label htmlFor="wine_name">Wine name *</Label>
                <Input
                  id="wine_name"
                  required
                  value={wineName}
                  onChange={(e) => setWineName(e.target.value)}
                  placeholder="e.g. Domaine Arlaud Morey-St-Denis 1er Cru"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label htmlFor="vintage">Vintage</Label>
                  <Input
                    id="vintage"
                    value={vintage}
                    onChange={(e) => setVintage(e.target.value)}
                    placeholder="2019 or NV"
                  />
                </div>
                <div>
                  <Label htmlFor="region">Region</Label>
                  <Input
                    id="region"
                    value={region}
                    onChange={(e) => setRegion(e.target.value)}
                    placeholder="Burgundy"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="mode">Verification mode</Label>
                <Select
                  id="mode"
                  value={mode}
                  onChange={(e) => setMode(e.target.value as 'hybrid_fast' | 'hybrid_strict')}
                >
                  <option value="hybrid_fast">Hybrid Fast — Gemini only (~25s)</option>
                  <option value="hybrid_strict">Hybrid Strict — Gemini + Qwen (~40s)</option>
                </Select>
              </div>

              <Button type="submit" loading={loading} className="w-full" size="lg">
                {loading ? 'Analyzing…' : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    Verify photo
                  </>
                )}
              </Button>
            </form>
          </Card>

          <Card className="p-5">
            <div className="text-xs font-semibold uppercase tracking-wider text-fg-muted mb-3">
              Quick presets
            </div>
            <div className="space-y-2">
              {PRESETS.map((p) => (
                <button
                  key={p.name}
                  onClick={() => loadPreset(p)}
                  className="w-full text-left p-3 rounded-lg ring-1 ring-border hover:ring-primary/30 hover:bg-primary-soft/30 transition-all group"
                >
                  <div className="text-sm text-fg font-medium leading-snug group-hover:text-primary transition-colors line-clamp-2">
                    {p.name}
                  </div>
                  <div className="text-xs text-fg-subtle mt-0.5">
                    {p.vintage} · {p.region}
                  </div>
                </button>
              ))}
            </div>
          </Card>
        </div>

        {/* Result */}
        <div className="min-w-0">
          {error && (
            <Card className="p-4 ring-danger/30 bg-danger-soft text-danger text-sm">
              {error}
            </Card>
          )}

          {loading && <LoadingSkeleton />}

          {!loading && !result && !error && <EmptyState />}

          {result && <AnalysisResultPanel data={result} />}
        </div>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <Card className="border-2 border-dashed bg-transparent ring-0 border-border min-h-[400px] flex flex-col items-center justify-center text-center p-10">
      <div className="h-12 w-12 rounded-full bg-bg-muted flex items-center justify-center mb-4">
        <Sparkles className="h-5 w-5 text-fg-subtle" />
      </div>
      <h3 className="font-medium text-fg mb-1">Ready when you are</h3>
      <p className="text-sm text-fg-muted max-w-xs">
        Enter a wine name on the left, or pick a preset to see how the pipeline handles a known SKU.
      </p>
    </Card>
  );
}

function LoadingSkeleton() {
  return (
    <Card className="overflow-hidden">
      <div className="grid grid-cols-1 md:grid-cols-[280px_1fr]">
        <div className="aspect-square md:aspect-auto md:min-h-[280px] animate-shimmer" />
        <div className="p-6 space-y-4">
          <div className="flex items-center gap-2">
            <div className="h-5 w-20 rounded animate-shimmer" />
            <div className="h-4 w-24 rounded animate-shimmer" />
          </div>
          <div className="h-6 w-3/4 rounded animate-shimmer" />
          <div className="h-4 w-1/2 rounded animate-shimmer" />
          <div className="grid grid-cols-2 gap-3 pt-2">
            <div className="h-16 rounded animate-shimmer" />
            <div className="h-16 rounded animate-shimmer" />
          </div>
          <div className="flex items-center gap-2 text-xs text-fg-muted pt-3">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Searching · screening · verifying…
          </div>
        </div>
      </div>
    </Card>
  );
}

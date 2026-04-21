'use client';

import { useState } from 'react';
import { Plus, Trash2, Sparkles, Download, RotateCcw, Layers } from 'lucide-react';
import { PageHeader } from '@/components/PageHeader';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input, Select } from '@/components/ui/Input';
import { BatchResultsTable } from '@/components/BatchResultsTable';
import { BatchProgressList } from '@/components/BatchProgressList';
import { createBatchJob, pollBatchJob } from '@/lib/api';
import { AnalysisResult, WineSKUInput } from '@/lib/types';

const TEST_SKUS: WineSKUInput[] = [
  { wine_name: 'Domaine Rossignol-Trapet Latricieres-Chambertin Grand Cru', vintage: '2017', region: 'Burgundy' },
  { wine_name: "Domaine Arlaud Morey-St-Denis 'Monts Luisants' 1er Cru", vintage: '2019', region: 'Burgundy' },
  { wine_name: 'Domaine Taupenot-Merme Charmes-Chambertin Grand Cru', vintage: '2018', region: 'Burgundy' },
  { wine_name: 'Château Fonroque Saint-Émilion Grand Cru Classé', vintage: '2016', region: 'Bordeaux' },
  { wine_name: 'Eric Rodez Cuvée des Crayères Blanc de Noirs', vintage: 'NV', region: 'Champagne' },
  { wine_name: "Domaine du Tunnel Cornas 'Vin Noir'", vintage: '2018', region: 'Northern Rhône' },
  { wine_name: "Poderi Colla Barolo 'Bussia Dardi Le Rose'", vintage: '2016', region: 'Piedmont' },
  { wine_name: 'Arnot-Roberts Trousseau Gris Watson Ranch', vintage: '2020', region: 'Sonoma' },
  { wine_name: 'Brokenwood Graveyard Vineyard Shiraz', vintage: '2015', region: 'Hunter Valley' },
  { wine_name: "Domaine Weinbach Riesling 'Clos des Capucins' Vendanges Tardives", vintage: '2017', region: 'Alsace' },
];

export default function BatchPage() {
  const [wines, setWines] = useState<WineSKUInput[]>([{ wine_name: '' }]);
  const [results, setResults] = useState<AnalysisResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<'hybrid_fast' | 'hybrid_strict'>('hybrid_fast');
  const [progress, setProgress] = useState({ completed: 0, total: 0 });
  const [incrementalResults, setIncrementalResults] = useState<AnalysisResult[]>([]);
  const [validWines, setValidWines] = useState<WineSKUInput[]>([]);

  const addWine = () => setWines([...wines, { wine_name: '' }]);
  const removeWine = (i: number) => setWines(wines.filter((_, idx) => idx !== i));
  const updateWine = (i: number, field: keyof WineSKUInput, value: string) => {
    const next = [...wines];
    next[i] = { ...next[i], [field]: value };
    setWines(next);
  };
  const loadTestSet = () => {
    setWines([...TEST_SKUS]);
    setResults(null);
    setError(null);
  };
  const clear = () => {
    setWines([{ wine_name: '' }]);
    setResults(null);
    setError(null);
  };

  const handleAnalyze = async () => {
    const valid = wines.filter((w) => w.wine_name.trim());
    if (valid.length === 0) {
      setError('Please enter at least one wine name');
      return;
    }
    setValidWines(valid);
    setLoading(true);
    setError(null);
    setResults(null);
    setIncrementalResults([]);
    setProgress({ completed: 0, total: valid.length });

    try {
      const job = await createBatchJob({ wines: valid, analyzer_mode: mode });
      const out = await pollBatchJob(
        job.job_id,
        (c, t, partialResults) => {
          setProgress({ completed: c, total: t });
          setIncrementalResults(partialResults);
        }
      );
      setResults(out);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Batch analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const downloadJson = () => {
    if (!results) return;
    const blob = new Blob([JSON.stringify(results, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `batch_results_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };


  return (
    <div>
      <PageHeader
        eyebrow="Batch · Async jobs"
        title="Batch verification"
        description="Submit a list of SKUs. Each wine takes ~25–40s. Results stream as they complete; the run keeps going even if you close the tab."
        actions={
          <>
            {results && (
              <Button variant="outline" onClick={downloadJson}>
                <Download className="h-4 w-4" />
                JSON
              </Button>
            )}
            <Button variant="outline" onClick={loadTestSet} disabled={loading}>
              <Layers className="h-4 w-4" />
              Load test set
            </Button>
          </>
        }
      />

      <div className="space-y-6">
        {/* Wines list */}
        <Card className="overflow-hidden">
          <div className="flex items-center justify-between p-5 border-b border-border">
            <div>
              <h3 className="text-sm font-semibold text-fg">
                Wines ({wines.length})
              </h3>
              <p className="text-xs text-fg-muted mt-0.5">
                Edit, remove, or add new SKUs below
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Select
                value={mode}
                onChange={(e) => setMode(e.target.value as 'hybrid_fast' | 'hybrid_strict')}
                className="w-44 h-8 text-xs"
                disabled={loading}
              >
                <option value="hybrid_fast">Fast (Gemini)</option>
                <option value="hybrid_strict">Strict (Gemini+Qwen)</option>
              </Select>
              <Button variant="ghost" size="sm" onClick={clear} disabled={loading}>
                <RotateCcw className="h-3.5 w-3.5" />
                Clear
              </Button>
            </div>
          </div>

          <div className="divide-y divide-border">
            {wines.map((w, i) => (
              <div
                key={i}
                className="grid grid-cols-[auto_1fr_120px_140px_auto] items-center gap-3 px-5 py-3 hover:bg-bg-subtle/50 transition-colors group"
              >
                <span className="text-xs font-mono text-fg-subtle w-6 text-right tabular-nums">
                  {String(i + 1).padStart(2, '0')}
                </span>
                <Input
                  value={w.wine_name}
                  onChange={(e) => updateWine(i, 'wine_name', e.target.value)}
                  placeholder="Wine name (producer + appellation + vineyard)"
                  disabled={loading}
                />
                <Input
                  value={w.vintage || ''}
                  onChange={(e) => updateWine(i, 'vintage', e.target.value)}
                  placeholder="Vintage"
                  disabled={loading}
                />
                <Input
                  value={w.region || ''}
                  onChange={(e) => updateWine(i, 'region', e.target.value)}
                  placeholder="Region"
                  disabled={loading}
                />
                <button
                  onClick={() => removeWine(i)}
                  disabled={loading || wines.length === 1}
                  className="p-1.5 rounded text-fg-subtle hover:text-danger hover:bg-danger-soft transition-colors disabled:opacity-0 group-hover:opacity-100 opacity-0"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>

          <div className="p-5 border-t border-border flex items-center justify-between gap-3 flex-wrap">
            <Button variant="ghost" size="sm" onClick={addWine} disabled={loading}>
              <Plus className="h-3.5 w-3.5" />
              Add wine
            </Button>
            <div className="flex items-center gap-3">
              {!loading && (
                <span className="text-xs text-fg-muted">
                  ~{Math.ceil(wines.length * 0.5)} min estimated
                </span>
              )}
              <Button onClick={handleAnalyze} loading={loading} disabled={loading}>
                <Sparkles className="h-4 w-4" />
                Analyze {wines.length} {wines.length === 1 ? 'wine' : 'wines'}
              </Button>
            </div>
          </div>

          {/* Progress - Per-element status */}
          {loading && progress.total > 0 && (
            <div className="border-t border-border">
              <BatchProgressList
                wines={validWines}
                results={incrementalResults}
                completed={progress.completed}
                total={progress.total}
              />
            </div>
          )}
        </Card>

        {error && (
          <Card className="p-4 ring-danger/30 bg-danger-soft text-danger text-sm">
            {error}
          </Card>
        )}

        {(results || incrementalResults.length > 0) && (
          <BatchResultsTable results={results || incrementalResults} />
        )}
      </div>
    </div>
  );
}

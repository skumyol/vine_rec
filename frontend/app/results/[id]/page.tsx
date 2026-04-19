'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { ResultSummaryCard } from '@/components/ResultSummaryCard';
import { FieldMatchTable } from '@/components/FieldMatchTable';
import { CandidateStrip } from '@/components/CandidateStrip';
import { DebugAccordion } from '@/components/DebugAccordion';
import { getResult, exportResultJson } from '@/lib/api';
import { RunDetail } from '@/lib/types';

export default function ResultPage() {
  const params = useParams();
  const runId = params.id as string;

  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!runId) return;

    const fetchResult = async () => {
      try {
        const data = await getResult(runId);
        setDetail(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load result');
      } finally {
        setLoading(false);
      }
    };

    fetchResult();
  }, [runId]);

  const handleExport = async () => {
    try {
      const data = await exportResultJson(runId);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `result-${runId}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert('Export failed: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="text-center py-12 text-gray-500">Loading...</div>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error || 'Result not found'}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Analysis Result</h1>
          <p className="text-sm text-gray-500">Run ID: {runId}</p>
        </div>
        <button
          onClick={handleExport}
          className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-md text-sm font-medium"
        >
          Export JSON
        </button>
      </div>

      <div className="space-y-4">
        <ResultSummaryCard result={detail.result} />
        <FieldMatchTable parsedSku={detail.result.parsed_sku} />
        <CandidateStrip candidates={detail.result.top_candidates} />
        <DebugAccordion result={detail.result} />

        {detail.candidates_count > 0 && (
          <div className="text-sm text-gray-500 text-center">
            Processed {detail.candidates_count} candidates
            {detail.processing_time_ms && ` in ${detail.processing_time_ms}ms`}
          </div>
        )}
      </div>
    </div>
  );
}

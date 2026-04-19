'use client';

import { useState } from 'react';
import { AnalysisResult } from '@/lib/types';

interface DebugAccordionProps {
  result: AnalysisResult;
}

export function DebugAccordion({ result }: DebugAccordionProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="border rounded-lg bg-gray-50">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-100 transition-colors"
      >
        <span className="font-medium text-sm text-gray-700">Debug Info</span>
        <svg
          className={`w-4 h-4 text-gray-500 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="p-3 border-t bg-white">
          <div className="space-y-4 text-sm">
            {/* Raw Input */}
            <div>
              <h4 className="font-medium text-gray-600 mb-1">Raw Input</h4>
              <pre className="bg-gray-50 p-2 rounded text-xs overflow-auto">
                {JSON.stringify(result.input, null, 2)}
              </pre>
            </div>

            {/* Parsed SKU */}
            <div>
              <h4 className="font-medium text-gray-600 mb-1">Parsed SKU</h4>
              <pre className="bg-gray-50 p-2 rounded text-xs overflow-auto">
                {JSON.stringify(result.parsed_sku, null, 2)}
              </pre>
            </div>

            {/* Top Candidates */}
            <div>
              <h4 className="font-medium text-gray-600 mb-1">Top Candidates ({result.top_candidates.length})</h4>
              <pre className="bg-gray-50 p-2 rounded text-xs overflow-auto max-h-40">
                {JSON.stringify(result.top_candidates, null, 2)}
              </pre>
            </div>

            {/* Metadata */}
            <div className="grid grid-cols-2 gap-4 text-xs text-gray-500">
              <div>Analyzer Mode: <span className="font-medium">{result.analyzer_mode}</span></div>
              <div>Created: <span className="font-medium">{new Date(result.created_at).toLocaleString()}</span></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

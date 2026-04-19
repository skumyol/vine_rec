'use client';

import { AnalysisResult } from '@/lib/types';

interface ResultSummaryCardProps {
  result: AnalysisResult;
}

export function ResultSummaryCard({ result }: ResultSummaryCardProps) {
  const verdictColor: Record<string, string> = {
    PASS: 'bg-green-100 text-green-800 border-green-200',
    REVIEW: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    FAIL: 'bg-red-100 text-red-800 border-red-200',
    NO_IMAGE: 'bg-gray-100 text-gray-800 border-gray-200',
  };
  const verdictClass = verdictColor[result.verdict] || verdictColor.NO_IMAGE;

  return (
    <div className="bg-white border rounded-lg p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Analysis Result</h2>
        <span className={`px-3 py-1 rounded-full text-sm font-medium border ${verdictClass}`}>
          {result.verdict}
        </span>
      </div>

      <div className="space-y-4">
        {/* Wine Info */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Wine:</span>
            <p className="font-medium">{result.input.wine_name}</p>
          </div>
          <div>
            <span className="text-gray-500">Vintage:</span>
            <p className="font-medium">{result.input.vintage || 'N/A'}</p>
          </div>
          <div>
            <span className="text-gray-500">Producer:</span>
            <p className="font-medium">{result.parsed_sku.producer || 'N/A'}</p>
          </div>
          <div>
            <span className="text-gray-500">Appellation:</span>
            <p className="font-medium">{result.parsed_sku.appellation || 'N/A'}</p>
          </div>
        </div>

        {/* Confidence Bar */}
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-500">Confidence</span>
            <span className="font-medium">{result.confidence.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full ${
                result.confidence >= 90
                  ? 'bg-green-500'
                  : result.confidence >= 75
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
              }`}
              style={{ width: `${result.confidence}%` }}
            />
          </div>
        </div>

        {/* Selected Image */}
        {result.selected_image_url ? (
          <div className="mt-4">
            <span className="text-gray-500 text-sm">Selected Image:</span>
            <div className="mt-2 border rounded-lg overflow-hidden">
              <img
                src={result.selected_image_url}
                alt={result.input.wine_name}
                className="w-full h-48 object-contain bg-gray-50"
              />
            </div>
          </div>
        ) : (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg text-center text-gray-500">
            No suitable image found
            {result.reason && <p className="text-sm mt-2">{result.reason}</p>}
          </div>
        )}

        {/* Reason */}
        {result.reason && result.selected_image_url && (
          <p className="text-sm text-gray-600">{result.reason}</p>
        )}
      </div>
    </div>
  );
}

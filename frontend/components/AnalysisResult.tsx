'use client';

import { useState } from 'react';
import { Check, X, AlertCircle, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';

interface AnalysisResultProps {
  data: {
    input: {
      wine_name: string;
      vintage?: string;
      format?: string;
      region?: string;
    };
    parsed_sku: {
      producer?: string;
      appellation?: string;
      vineyard?: string;
      classification?: string;
      vintage?: string;
    };
    selected_image_url?: string;
    confidence: number;
    verdict: string;
    reason: string;
    analyzer_mode: string;
    top_candidates: Array<{
      url: string;
      score: number;
      verdict: string;
      domain: string;
    }>;
  };
}

export function AnalysisResult({ data }: AnalysisResultProps) {
  const isPass = data.verdict === 'PASS';
  const isNoImage = data.verdict === 'NO_IMAGE';
  const [showDebug, setShowDebug] = useState(false);

  // Verdict badge styles - clean, flat, obvious
  const getVerdictStyle = (verdict: string) => {
    switch (verdict) {
      case 'PASS':
        return 'bg-green-600 text-white';
      case 'NO_IMAGE':
        return 'bg-gray-400 text-white';
      case 'REVIEW':
        return 'bg-yellow-500 text-white';
      default:
        return 'bg-red-600 text-white';
    }
  };

  const getVerdictIcon = (verdict: string) => {
    switch (verdict) {
      case 'PASS':
        return <Check className="w-4 h-4" />;
      case 'NO_IMAGE':
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <X className="w-4 h-4" />;
    }
  };

  return (
    <div className="border border-gray-200">
      {/* Hero Section: Bottle image + Verdict - THE ANSWER FIRST */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-0">
        {/* Left: Bottle image as hero */}
        <div className="bg-gray-50 p-6 flex items-center justify-center min-h-[320px]">
          {isPass && data.selected_image_url ? (
            <div className="relative w-full h-full flex items-center justify-center">
              <img 
                src={data.selected_image_url} 
                alt="Verified bottle"
                className="max-h-[400px] max-w-full object-contain"
              />
              <a 
                href={data.selected_image_url}
                target="_blank"
                rel="noopener noreferrer"
                className="absolute top-0 right-0 p-2 bg-white border border-gray-200 hover:bg-gray-100 transition-colors"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          ) : (
            <div className="text-center">
              <div className="w-24 h-32 border-2 border-dashed border-gray-300 mx-auto mb-4 flex items-center justify-center">
                <span className="text-gray-400 text-xs uppercase">No Image</span>
              </div>
              <p className="text-sm text-gray-500">
                No candidate met verification threshold
              </p>
            </div>
          )}
        </div>

        {/* Right: Verdict panel */}
        <div className="p-6 border-l border-gray-200">
          {/* Wine name as headline */}
          <h2 className="text-xl font-bold text-black leading-tight mb-4">
            {data.input.wine_name}
          </h2>

          {/* Verdict badge - bold and clear */}
          <div className={`inline-flex items-center gap-2 px-4 py-2 text-sm font-bold uppercase tracking-wide ${getVerdictStyle(data.verdict)}`}>
            {getVerdictIcon(data.verdict)}
            {data.verdict === 'NO_IMAGE' ? 'NO IMAGE' : data.verdict}
          </div>

          {/* Confidence - large and clear */}
          <div className="mt-6">
            <p className="text-xs font-bold text-gray-900 uppercase tracking-wide mb-1">Confidence</p>
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-black">
                {data.confidence.toFixed(0)}
              </span>
              <span className="text-lg font-bold text-gray-400">/ 100</span>
            </div>
          </div>

          {/* One-line reason */}
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-sm text-gray-600">{data.reason}</p>
          </div>

          {/* Parsed info - compact */}
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs">
              {data.parsed_sku.producer && (
                <span><strong>Producer:</strong> {data.parsed_sku.producer}</span>
              )}
              {data.parsed_sku.vintage && (
                <span><strong>Vintage:</strong> {data.parsed_sku.vintage}</span>
              )}
            </div>
            {(data.parsed_sku.appellation || data.parsed_sku.vineyard || data.parsed_sku.classification) && (
              <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs mt-1 text-gray-500">
                {data.parsed_sku.appellation && <span>{data.parsed_sku.appellation}</span>}
                {data.parsed_sku.vineyard && <span>{data.parsed_sku.vineyard}</span>}
                {data.parsed_sku.classification && <span>{data.parsed_sku.classification}</span>}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Debug section - collapsible, hidden by default */}
      {data.top_candidates.length > 0 && (
        <div className="border-t border-gray-200">
          <button
            onClick={() => setShowDebug(!showDebug)}
            className="w-full flex items-center justify-between px-6 py-3 bg-gray-50 hover:bg-gray-100 transition-colors text-xs font-bold uppercase tracking-wide text-gray-700"
          >
            <span>Technical Details ({data.top_candidates.length} candidates)</span>
            {showDebug ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {showDebug && (
            <div className="px-6 py-4 bg-gray-50">
              <div className="space-y-2">
                {data.top_candidates.slice(0, 10).map((candidate, index) => (
                  <div 
                    key={index}
                    className="flex items-center justify-between py-2 border-b border-gray-200 last:border-0"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="text-xs font-bold text-gray-400 w-5">{index + 1}</span>
                      <div className="min-w-0">
                        <p className="text-xs font-medium truncate">{candidate.domain}</p>
                        <p className="text-[10px] text-gray-500 truncate max-w-[200px]">
                          {candidate.url.slice(0, 50)}...
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold">
                        {candidate.score.toFixed(0)}
                      </span>
                      <span className={`px-2 py-0.5 text-[10px] font-bold uppercase ${getVerdictStyle(candidate.verdict)}`}>
                        {candidate.verdict === 'NO_IMAGE' ? 'NONE' : candidate.verdict}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              {data.top_candidates.length > 10 && (
                <p className="text-xs text-gray-400 mt-2">
                  + {data.top_candidates.length - 10} more candidates
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

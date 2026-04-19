'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { Search, ChevronDown } from 'lucide-react';

interface Wine {
  id: string;
  sku: string;
  name: string;
  vintage?: string;
  producer: string;
  region?: string;
  country?: string;
  price_hkd: number;
  type?: string;
  image?: string;
}

interface AnalysisFormProps {
  onSubmit: (data: {
    wine_name: string;
    vintage?: string;
    format?: string;
    region?: string;
    analyzer_mode: string;
  }) => void;
  loading: boolean;
}

const ANALYZER_MODES = [
  { value: 'hybrid_fast', label: 'Fast' },
  { value: 'hybrid_strict', label: 'Strict' },
  { value: 'gemini', label: 'Gemini' },
  { value: 'qwen_vl', label: 'Qwen' },
  { value: 'opencv_only', label: 'Debug' },
];

export function AnalysisForm({ onSubmit, loading }: AnalysisFormProps) {
  const [wineName, setWineName] = useState('');
  const [vintage, setVintage] = useState('');
  const [format, setFormat] = useState('750ml');
  const [region, setRegion] = useState('');
  const [analyzerMode, setAnalyzerMode] = useState('hybrid_strict');

  // Wine dropdown state
  const [wineSearchQuery, setWineSearchQuery] = useState('');
  const [wineResults, setWineResults] = useState<Wine[]>([]);
  const [wineDropdownOpen, setWineDropdownOpen] = useState(false);
  const [wineLoading, setWineLoading] = useState(false);
  const wineDropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch('/api/analyzer-modes')
      .then(res => res.json())
      .then(data => {
        setAnalyzerMode(data.default);
      })
      .catch(console.error);
  }, []);

  // Search wines from VinoBuzz
  const searchWines = useCallback(async (query: string) => {
    if (!query.trim()) {
      setWineResults([]);
      return;
    }
    setWineLoading(true);
    try {
      const res = await fetch(`/api/wines/search?q=${encodeURIComponent(query)}&limit=20`);
      if (res.ok) {
        const data = await res.json();
        setWineResults(data.wines || []);
      }
    } catch (err) {
      console.error('Failed to search wines:', err);
    } finally {
      setWineLoading(false);
    }
  }, []);

  // Debounced search
  useEffect(() => {
    const timeout = setTimeout(() => {
      if (wineSearchQuery.trim()) {
        searchWines(wineSearchQuery);
      }
    }, 300);
    return () => clearTimeout(timeout);
  }, [wineSearchQuery, searchWines]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wineDropdownRef.current && !wineDropdownRef.current.contains(event.target as Node)) {
        setWineDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleWineSelect = (wine: Wine) => {
    setWineName(wine.name);
    if (wine.vintage) setVintage(wine.vintage);
    if (wine.region) setRegion(wine.region);
    setWineSearchQuery('');
    setWineResults([]);
    setWineDropdownOpen(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!wineName.trim()) return;
    
    onSubmit({
      wine_name: wineName,
      vintage: vintage || undefined,
      format: format || undefined,
      region: region || undefined,
      analyzer_mode: analyzerMode,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="border border-gray-200 p-6">
      {/* Compact, functional inputs - no decorative icons */}
      <div className="space-y-4">
        <div className="relative" ref={wineDropdownRef}>
          <label className="block text-xs font-bold text-gray-900 uppercase tracking-wide mb-1.5">
            Wine Name
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={wineName}
              onChange={(e) => setWineName(e.target.value)}
              placeholder="Domaine Rossignol-Trapet Latricieres-Chambertin"
              className="flex-1 px-3 py-2.5 bg-gray-50 border border-gray-200 text-sm focus:outline-none focus:border-black focus:bg-white transition-colors"
              required
            />
            <button
              type="button"
              onClick={() => setWineDropdownOpen(!wineDropdownOpen)}
              className="px-3 py-2.5 bg-gray-100 border border-gray-200 hover:bg-gray-200 transition-colors flex items-center gap-1"
              title="Select from VinoBuzz"
            >
              <span className="text-xs font-medium">VinoBuzz</span>
              <ChevronDown className="w-4 h-4" />
            </button>
          </div>

          {/* Wine dropdown */}
          {wineDropdownOpen && (
            <div className="absolute z-50 top-full left-0 right-0 mt-1 bg-white border border-gray-200 shadow-lg max-h-80 overflow-auto">
              <div className="sticky top-0 bg-white border-b border-gray-200 p-2">
                <input
                  type="text"
                  value={wineSearchQuery}
                  onChange={(e) => setWineSearchQuery(e.target.value)}
                  placeholder="Search VinoBuzz wines..."
                  className="w-full px-3 py-2 bg-gray-50 border border-gray-200 text-sm focus:outline-none focus:border-black"
                  autoFocus
                />
              </div>
              {wineLoading && (
                <div className="p-4 text-center text-sm text-gray-500">Loading...</div>
              )}
              {!wineLoading && wineResults.length === 0 && wineSearchQuery.trim() && (
                <div className="p-4 text-center text-sm text-gray-500">No wines found</div>
              )}
              {!wineLoading && wineResults.length === 0 && !wineSearchQuery.trim() && (
                <div className="p-4 text-center text-sm text-gray-500">Type to search wines</div>
              )}
              {wineResults.map((wine) => (
                <button
                  key={wine.id}
                  type="button"
                  onClick={() => handleWineSelect(wine)}
                  className="w-full text-left px-3 py-2.5 hover:bg-gray-50 border-b border-gray-100 last:border-0 transition-colors"
                >
                  <div className="font-medium text-sm text-gray-900 leading-tight">
                    {wine.name}
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    {wine.producer}
                    {wine.vintage && ` • ${wine.vintage}`}
                    {wine.region && ` • ${wine.region}`}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="block text-xs font-bold text-gray-900 uppercase tracking-wide mb-1.5">
              Vintage
            </label>
            <input
              type="text"
              value={vintage}
              onChange={(e) => setVintage(e.target.value)}
              placeholder="2017"
              className="w-full px-3 py-2.5 bg-gray-50 border border-gray-200 text-sm focus:outline-none focus:border-black focus:bg-white transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-900 uppercase tracking-wide mb-1.5">
              Format
            </label>
            <input
              type="text"
              value={format}
              onChange={(e) => setFormat(e.target.value)}
              placeholder="750ml"
              className="w-full px-3 py-2.5 bg-gray-50 border border-gray-200 text-sm focus:outline-none focus:border-black focus:bg-white transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-900 uppercase tracking-wide mb-1.5">
              Region
            </label>
            <input
              type="text"
              value={region}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setRegion(e.target.value)}
              placeholder="Burgundy"
              className="w-full px-3 py-2.5 bg-gray-50 border border-gray-200 text-sm focus:outline-none focus:border-black focus:bg-white transition-colors"
            />
          </div>
        </div>

        {/* Segmented control for analyzer mode */}
        <div>
          <label className="block text-xs font-bold text-gray-900 uppercase tracking-wide mb-2">
            Mode
          </label>
          <div className="flex flex-wrap gap-1">
            {ANALYZER_MODES.map(mode => (
              <button
                key={mode.value}
                type="button"
                onClick={() => setAnalyzerMode(mode.value)}
                className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                  analyzerMode === mode.value
                    ? 'bg-black text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {mode.label}
              </button>
            ))}
          </div>
        </div>

        {/* Bold CTA button */}
        <button
          type="submit"
          disabled={loading || !wineName.trim()}
          className="w-full flex items-center justify-center px-4 py-3 bg-black text-white font-bold text-sm uppercase tracking-wide hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <span className="animate-pulse">VERIFYING</span>
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <Search className="w-4 h-4" />
              VERIFY SKU
            </span>
          )}
        </button>
      </div>
    </form>
  );
}

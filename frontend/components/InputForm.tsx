'use client';

import { useState, useEffect, useRef } from 'react';
import { Wine, WineSKUInput } from '@/lib/types';
import { searchWines } from '@/lib/api';

interface InputFormProps {
  onSubmit: (data: WineSKUInput) => void;
  loading?: boolean;
  initialData?: Partial<WineSKUInput>;
}

export function InputForm({ onSubmit, loading = false, initialData }: InputFormProps) {
  const [wineName, setWineName] = useState(initialData?.wine_name || '');
  const [vintage, setVintage] = useState(initialData?.vintage || '');
  const [format, setFormat] = useState(initialData?.format || '750ml');
  const [region, setRegion] = useState(initialData?.region || '');
  const [searchQuery, setSearchQuery] = useState('');
  const [wines, setWines] = useState<Wine[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Search wines when query changes
  useEffect(() => {
    const search = async () => {
      if (searchQuery.length < 2) {
        setWines([]);
        return;
      }
      setIsSearching(true);
      try {
        const results = await searchWines(searchQuery);
        setWines(results);
      } catch (err) {
        console.error('Search error:', err);
      } finally {
        setIsSearching(false);
      }
    };

    const timeout = setTimeout(search, 300);
    return () => clearTimeout(timeout);
  }, [searchQuery]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelectWine = (wine: Wine) => {
    setWineName(wine.full_name);
    setVintage(wine.vintage?.toString() || '');
    setRegion(wine.region);
    setSearchQuery('');
    setShowDropdown(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!wineName.trim()) return;
    onSubmit({
      wine_name: wineName,
      vintage: vintage || undefined,
      format: format || undefined,
      region: region || undefined,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Wine Search Dropdown */}
      <div className="relative" ref={dropdownRef}>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Search Wine
        </label>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => {
            setSearchQuery(e.target.value);
            setShowDropdown(true);
          }}
          onFocus={() => setShowDropdown(true)}
          placeholder="Type to search wines..."
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
        />
        {showDropdown && (isSearching || wines.length > 0) && (
          <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
            {isSearching && (
              <div className="px-3 py-2 text-sm text-gray-500">Searching...</div>
            )}
            {!isSearching && wines.length === 0 && searchQuery.length >= 2 && (
              <div className="px-3 py-2 text-sm text-gray-500">No wines found</div>
            )}
            {wines.map((wine) => (
              <button
                key={wine.id}
                type="button"
                onClick={() => handleSelectWine(wine)}
                className="w-full text-left px-3 py-2 hover:bg-gray-100 border-b border-gray-100 last:border-0"
              >
                <div className="font-medium text-sm">{wine.full_name}</div>
                <div className="text-xs text-gray-500">
                  {wine.producer} · {wine.appellation} · {wine.vintage || 'NV'}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Wine Name */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Wine Name *
        </label>
        <input
          type="text"
          value={wineName}
          onChange={(e) => setWineName(e.target.value)}
          placeholder="Enter wine name"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          required
        />
      </div>

      <div className="grid grid-cols-3 gap-4">
        {/* Vintage */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Vintage
          </label>
          <input
            type="text"
            value={vintage}
            onChange={(e) => setVintage(e.target.value)}
            placeholder="2020"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Format */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Format
          </label>
          <select
            value={format}
            onChange={(e) => setFormat(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="750ml">750ml</option>
            <option value="375ml">375ml</option>
            <option value="1.5L">1.5L (Magnum)</option>
            <option value="3L">3L (Double Magnum)</option>
            <option value="6L">6L (Imperial)</option>
          </select>
        </div>

        {/* Region */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Region
          </label>
          <input
            type="text"
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            placeholder="Burgundy"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      <button
        type="submit"
        disabled={loading || !wineName.trim()}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? 'Analyzing...' : 'Analyze Wine'}
      </button>
    </form>
  );
}

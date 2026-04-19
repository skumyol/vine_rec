'use client';

import { useState, useEffect } from 'react';
import { Activity } from 'lucide-react';

interface HealthData {
  status: string;
  services: {
    gemini: { available: boolean; model?: string };
    qwen: { available: boolean; model?: string };
    search: { provider: string; configured: boolean };
    ocr: { engine: string };
  };
  config: {
    default_analyzer_mode: string;
    pass_threshold: number;
    review_threshold: number;
  };
}

export function SystemStatus() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => {
        setHealth(data);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, []);

  // Compact inline status bar - minimal and functional
  return (
    <div className="flex items-center gap-4 py-2 border-b border-gray-200 text-xs">
      {loading ? (
        <span className="flex items-center gap-1.5 text-gray-400">
          <Activity className="w-3 h-3 animate-pulse" />
          Loading...
        </span>
      ) : !health ? (
        <span className="text-red-600 font-medium">System Offline</span>
      ) : (
        <>
          <span className="flex items-center gap-1.5">
            <span className={`w-2 h-2 ${health.services.gemini.available ? 'bg-green-500' : 'bg-gray-300'}`} />
            <span className={health.services.gemini.available ? 'text-gray-900' : 'text-gray-400'}>Gemini</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className={`w-2 h-2 ${health.services.qwen.available ? 'bg-green-500' : 'bg-gray-300'}`} />
            <span className={health.services.qwen.available ? 'text-gray-900' : 'text-gray-400'}>Qwen</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className={`w-2 h-2 ${health.services.search.configured ? 'bg-green-500' : 'bg-gray-300'}`} />
            <span className={health.services.search.configured ? 'text-gray-900' : 'text-gray-400'}>
              {health.services.search.provider}
            </span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 bg-green-500" />
            <span className="text-gray-900 uppercase">{health.services.ocr.engine}</span>
          </span>
          <span className="ml-auto text-gray-400">
            Pass: {health.config.pass_threshold} | Review: {health.config.review_threshold}
          </span>
        </>
      )}
    </div>
  );
}

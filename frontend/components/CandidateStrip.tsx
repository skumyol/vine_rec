'use client';

import { TopCandidate } from '@/lib/types';
import { getCandidateImageUrl, getCandidateScore } from '@/lib/candidate-utils';

interface CandidateStripProps {
  candidates: TopCandidate[];
}

export function CandidateStrip({ candidates }: CandidateStripProps) {
  if (!candidates || candidates.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg p-4 text-center text-gray-500">
        No candidate images found
      </div>
    );
  }

  return (
    <div className="bg-white border rounded-lg p-4">
      <h3 className="font-medium text-gray-900 mb-3">Top Candidates</h3>
      <div className="flex gap-3 overflow-x-auto pb-2">
        {candidates.map((candidate, index) => {
          const imageUrl = getCandidateImageUrl(candidate);
          const score = getCandidateScore(candidate);

          return (
            <div
              key={index}
              className="flex-shrink-0 w-32 border rounded-lg overflow-hidden bg-gray-50"
            >
              <div className="relative h-24 bg-gray-100">
                <img
                  src={imageUrl}
                  alt={`Candidate ${index + 1}`}
                  className="w-full h-full object-contain"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = '/placeholder-wine.png';
                  }}
                />
                <div className="absolute top-1 left-1 bg-black/50 text-white text-xs px-1.5 py-0.5 rounded">
                  #{index + 1}
                </div>
              </div>
              <div className="p-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium">{score.toFixed(1)}</span>
                  <span
                    className={`text-xs px-1.5 py-0.5 rounded ${
                      candidate.verdict === 'PASS'
                        ? 'bg-green-100 text-green-700'
                        : 'bg-red-100 text-red-700'
                    }`}
                  >
                    {candidate.verdict}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

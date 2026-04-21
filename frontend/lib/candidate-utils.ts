import { TopCandidate } from './types';

export function getCandidateImageUrl(candidate: TopCandidate): string {
  return candidate.image_url ?? candidate.url ?? '';
}

export function getCandidateScore(candidate: TopCandidate): number {
  return candidate.total_score ?? candidate.score ?? 0;
}

/** TypeScript type definitions for Wine Photo Verification API */

export interface WineSKUInput {
  wine_name: string;
  vintage?: string;
  format?: string;
  region?: string;
}

export interface ParsedSKU {
  raw_name: string;
  producer?: string;
  producer_normalized?: string;
  appellation?: string;
  appellation_normalized?: string;
  vineyard?: string;
  vineyard_normalized?: string;
  classification?: string;
  classification_normalized?: string;
  cuvee?: string;
  cuvee_normalized?: string;
  vintage?: string;
  format_ml?: number;
  region?: string;
  normalized_tokens: string[];
}

export interface AnalysisRequest {
  wine_name: string;
  vintage?: string;
  format?: string;
  region?: string;
  analyzer_mode: 'hybrid_fast' | 'hybrid_strict';
}

export interface BatchAnalysisRequest {
  wines: WineSKUInput[];
  analyzer_mode: 'hybrid_fast' | 'hybrid_strict';
}

export interface TopCandidate {
  image_url: string;
  total_score: number;
  verdict: string;
}

export interface AnalysisResult {
  input: WineSKUInput;
  parsed_sku: ParsedSKU;
  selected_image_url: string | null;
  confidence: number;
  verdict: 'PASS' | 'REVIEW' | 'FAIL' | 'NO_IMAGE';
  reason: string;
  analyzer_mode: string;
  top_candidates: TopCandidate[];
  created_at: string;
}

export interface Wine {
  id: number;
  name: string;
  full_name: string;
  producer: string;
  appellation: string;
  region: string;
  country: string;
  color: string;
  vintage?: number;
  bottle_size?: string;
}

export interface RunSummary {
  run_id: string;
  wine_name: string;
  vintage?: string;
  verdict: string;
  confidence: number;
  has_image: boolean;
  created_at: string;
}

export interface RunListResponse {
  runs: RunSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface RunDetail {
  run_id: string;
  result: AnalysisResult;
  candidates_count: number;
  processing_time_ms?: number;
}

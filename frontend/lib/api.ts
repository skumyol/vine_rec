/** API client for Wine Photo Verification backend */

import {
  AnalysisRequest,
  AnalysisResult,
  BatchAnalysisRequest,
  RunListResponse,
  RunDetail,
  Wine,
} from './types';

const API_BASE = '/api';

async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`API error: ${response.status} - ${error}`);
  }

  return response.json();
}

/** Analyze a single wine */
export async function analyzeWine(
  request: AnalysisRequest
): Promise<AnalysisResult> {
  return fetchApi<AnalysisResult>('/analyze/', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/** Analyze multiple wines in batch (sync - for small batches only) */
export async function analyzeBatch(
  request: BatchAnalysisRequest
): Promise<AnalysisResult[]> {
  return fetchApi<AnalysisResult[]>('/analyze/batch', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/** Create async batch job (returns immediately, use poll for results) */
export async function createBatchJob(
  request: BatchAnalysisRequest
): Promise<{ job_id: string; status: string; message: string }> {
  return fetchApi<{ job_id: string; status: string; message: string }>('/jobs/batch', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/** Poll for job status and results */
export async function getJobStatus(jobId: string): Promise<{
  id: string;
  status: string;
  total_wines: number;
  completed_wines: number;
  results: AnalysisResult[];
  errors: string[];
}> {
  return fetchApi(`/jobs/${jobId}`);
}

/** Poll batch job until complete */
export async function pollBatchJob(
  jobId: string,
  onProgress?: (completed: number, total: number) => void,
  pollInterval: number = 3000
): Promise<AnalysisResult[]> {
  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const job = await getJobStatus(jobId);
        
        if (onProgress) {
          onProgress(job.completed_wines, job.total_wines);
        }
        
        if (job.status === 'completed') {
          resolve(job.results);
        } else if (job.status === 'failed') {
          reject(new Error(`Job failed: ${job.errors.join(', ')}`));
        } else {
          // Still running, poll again
          setTimeout(poll, pollInterval);
        }
      } catch (error) {
        reject(error);
      }
    };
    
    poll();
  });
}

/** List analysis results with optional filters */
export async function listResults(
  page: number = 1,
  pageSize: number = 20,
  verdict?: string,
  wineName?: string
): Promise<RunListResponse> {
  const params = new URLSearchParams();
  params.append('page', page.toString());
  params.append('page_size', pageSize.toString());
  if (verdict) params.append('verdict', verdict);
  if (wineName) params.append('wine_name', wineName);

  return fetchApi<RunListResponse>(`/results/?${params.toString()}`);
}

/** Get detailed result for a specific run */
export async function getResult(runId: string): Promise<RunDetail> {
  return fetchApi<RunDetail>(`/results/${runId}`);
}

/** Export a single result as JSON */
export async function exportResultJson(runId: string): Promise<AnalysisResult> {
  return fetchApi<AnalysisResult>(`/results/${runId}/export/json`);
}

/** Export results as CSV */
export async function exportResultsCsv(runIds?: string[]): Promise<string> {
  const params = new URLSearchParams();
  if (runIds && runIds.length > 0) {
    params.append('run_ids', runIds.join(','));
  }

  const url = `${API_BASE}/results/export/csv?${params.toString()}`;
  const response = await fetch(url);

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Export error: ${response.status} - ${error}`);
  }

  return response.text();
}

/** Search wines from VinoBuzz */
export async function searchWines(query: string): Promise<Wine[]> {
  if (!query || query.length < 2) return [];

  const params = new URLSearchParams();
  params.append('q', query);

  return fetchApi<Wine[]>(`/wines/search?${params.toString()}`);
}

/** Get all wines (for dropdown) */
export async function getAllWines(): Promise<Wine[]> {
  return fetchApi<Wine[]>('/wines/');
}

/** Refresh wine cache */
export async function refreshWines(): Promise<{ message: string; count: number }> {
  return fetchApi<{ message: string; count: number }>('/wines/refresh', {
    method: 'POST',
  });
}

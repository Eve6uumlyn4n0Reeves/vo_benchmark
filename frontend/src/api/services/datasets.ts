/**
 * Datasets API service (services layer)
 * Aligns with backend /api/v1/datasets endpoints
 */

import { apiRequest } from '../httpClient';

export interface Sequence {
  name: string;
  path: string;
  frames?: number;
}

export interface Dataset {
  name: string;
  path: string;
  format?: string;
  type?: string;
  description?: string | null;
  total_frames?: number;
  sequences: Sequence[];
  sequences_info?: Sequence[];
  format_valid?: boolean;
  last_modified?: string | null;
  has_groundtruth?: boolean;
}

export interface DatasetListResponse {
  datasets: Dataset[];
  total_count: number;
  scan_paths: string[];
}

export interface DatasetValidationRequest {
  path: string;
}

export interface ValidationResult {
  valid: boolean;
  dataset_type?: string;
  issues: string[];
  suggestions: string[];
  statistics: Record<string, unknown>;
}

export const listDatasets = async (): Promise<DatasetListResponse> => {
  const resp = await apiRequest.get<DatasetListResponse>('/datasets/');
  return resp.data as unknown as DatasetListResponse;
};

export const validateDataset = async (req: DatasetValidationRequest): Promise<ValidationResult> => {
  const resp = await apiRequest.post<ValidationResult>('/datasets/validate', req);
  return resp.data as unknown as ValidationResult;
};


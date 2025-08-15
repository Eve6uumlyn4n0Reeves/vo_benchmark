/**
 * Centralized query keys for React Query
 * Following hierarchical structure for better cache management
 */

// Base query keys
export const queryKeys = {
  // Health endpoints
  health: ['health'] as const,
  healthDetailed: () => [...queryKeys.health, 'detailed'] as const,
  healthReady: () => [...queryKeys.health, 'ready'] as const,

  // Config endpoints
  config: ['config'] as const,
  configClient: () => [...queryKeys.config, 'client'] as const,
  configSystem: () => [...queryKeys.config, 'system'] as const,
  configAlgorithms: () => [...queryKeys.config, 'algorithms'] as const,
  configDiagnostics: () => [...queryKeys.config, 'diagnostics'] as const,

  // Experiments
  experiments: ['experiments'] as const,
  experimentsList: (params?: {
    page?: number;
    per_page?: number;
    q?: string;
    status?: string;
  }) => [...queryKeys.experiments, 'list', params] as const,
  experimentsDetail: (id: string) => [...queryKeys.experiments, 'detail', id] as const,
  experimentsHistory: (id: string) => [...queryKeys.experiments, 'history', id] as const,
  experimentsPreviewOutput: (params: { 
    dataset_path: string; 
    output_root?: string; 
  }) => [...queryKeys.experiments, 'preview-output', params] as const,

  // Results
  results: ['results'] as const,
  resultsOverview: (experimentId: string) => 
    [...queryKeys.results, 'overview', experimentId] as const,
  resultsDiagnose: (experimentId: string) => 
    [...queryKeys.results, 'diagnose', experimentId] as const,
  resultsAlgorithm: (experimentId: string, algorithmKey: string) => 
    [...queryKeys.results, 'algorithm', experimentId, algorithmKey] as const,
  resultsFrames: (
    experimentId: string, 
    algorithmKey: string, 
    params?: {
      page?: number;
      per_page?: number;
    }
  ) => [...queryKeys.results, 'frames', experimentId, algorithmKey, params] as const,
  resultsPrCurve: (experimentId: string, algorithmKey: string) => 
    [...queryKeys.results, 'pr-curve', experimentId, algorithmKey] as const,
  resultsTrajectory: (
    experimentId: string,
    algorithmKey: string,
    params?: { include_reference?: boolean }
  ) => [...queryKeys.results, 'trajectory', experimentId, algorithmKey, params] as const,

  // Tasks
  tasks: ['tasks'] as const,
  tasksList: (params?: Record<string, unknown>) => [...queryKeys.tasks, 'list', params] as const,
  tasksDetail: (taskId: string) => [...queryKeys.tasks, 'detail', taskId] as const,
  tasksLogs: (taskId: string) => [...queryKeys.tasks, 'logs', taskId] as const,

  // SSE Events
  events: ['events'] as const,
  eventsStream: () => [...queryKeys.events, 'stream'] as const,
} as const;

// Type helpers for query keys
export type QueryKey = typeof queryKeys;
export type ExperimentsListParams = Parameters<typeof queryKeys.experimentsList>[0];
export type ResultsFramesParams = Parameters<typeof queryKeys.resultsFrames>[2];

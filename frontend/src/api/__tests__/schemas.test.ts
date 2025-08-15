import { describe, it, expect } from '@jest/globals';
import {
  PRCurveResponseSchema,
  TrajectoryResponseSchema,
  FrameResultsResponseSchema,
  ExperimentsListResponseSchema,
  ClientConfigSchema,
  HealthResponseSchema,
  TaskResponseSchema,
  validateApiResponse,
} from '../schemas';

describe('API Schemas', () => {
  describe('PRCurveResponseSchema', () => {
    it('should validate valid PR curve response', () => {
      const validData = {
        algorithm: 'SIFT_STANDARD',
        precisions: [1.0, 0.9, 0.8],
        recalls: [0.1, 0.2, 0.3],
        thresholds: [0.9, 0.8, 0.7],
        auc_score: 0.85,
        optimal_threshold: 0.8,
        optimal_precision: 0.9,
        optimal_recall: 0.2,
        f1_scores: [0.18, 0.33, 0.46],
        max_f1_score: 0.46,
      };

      expect(() => PRCurveResponseSchema.parse(validData)).not.toThrow();
    });

    it('should handle empty arrays for no-data state', () => {
      const emptyData = {
        algorithm: 'SIFT_STANDARD',
        precisions: [],
        recalls: [],
        thresholds: [],
        auc_score: 0,
        optimal_threshold: 0,
        optimal_precision: 0,
        optimal_recall: 0,
        f1_scores: [],
        max_f1_score: 0,
      };

      expect(() => PRCurveResponseSchema.parse(emptyData)).not.toThrow();
    });

    it('should reject invalid precision values', () => {
      const invalidData = {
        algorithm: 'SIFT_STANDARD',
        precisions: [1.5], // Invalid: > 1
        recalls: [0.1],
        thresholds: [0.9],
        auc_score: 0.85,
        optimal_threshold: 0.8,
        optimal_precision: 0.9,
        optimal_recall: 0.2,
        f1_scores: [0.18],
        max_f1_score: 0.46,
      };

      expect(() => PRCurveResponseSchema.parse(invalidData)).toThrow();
    });
  });

  describe('TrajectoryResponseSchema', () => {
    it('should validate trajectory with poses only', () => {
      const validData = {
        poses: [{ x: 0, y: 0, z: 0 }, { x: 1, y: 1, z: 1 }],
      };

      expect(() => TrajectoryResponseSchema.parse(validData)).not.toThrow();
    });

    it('should validate trajectory with gt and ref', () => {
      const validData = {
        poses: [{ x: 0, y: 0, z: 0 }],
        gt: [{ x: 0, y: 0, z: 0 }],
        ref: [{ x: 0, y: 0, z: 0 }],
      };

      expect(() => TrajectoryResponseSchema.parse(validData)).not.toThrow();
    });

    it('should allow optional gt and ref fields', () => {
      const validData = {
        poses: [{ x: 0, y: 0, z: 0 }],
        // gt and ref are optional
      };

      const result = TrajectoryResponseSchema.parse(validData);
      expect(result.gt).toBeUndefined();
      expect(result.ref).toBeUndefined();
    });
  });

  describe('FrameResultsResponseSchema', () => {
    it('should validate frame results response', () => {
      const validData = {
        experiment_id: 'exp-123',
        algorithm_key: 'SIFT_STANDARD',
        sequence: 'seq-01',
        frames: [
          {
            frame_id: 'frame-001',
            timestamp: '2025-01-01T12:00:00Z',
            num_matches: 100,
            num_inliers: 80,
            inlier_ratio: 0.8,
            processing_time: 50.5,
            status: 'SUCCESS',
          },
        ],
        pagination: {
          page: 1,
          limit: 20,
          total: 100,
          total_pages: 5,
          has_next: true,
          has_previous: false,
        },
        summary: { avg_inlier_ratio: 0.75 },
      };

      expect(() => FrameResultsResponseSchema.parse(validData)).not.toThrow();
    });
  });

  describe('ClientConfigSchema', () => {
    it('should validate client config response', () => {
      const validData = {
        experiment: {
          defaultRuns: 3,
          defaultParallelJobs: 4,
          defaultMaxFeatures: 1000,
          defaultRansacThreshold: 1.0,
          defaultRansacConfidence: 0.99,
          defaultRansacMaxIters: 2000,
          defaultRatioThreshold: 0.8,
        },
        algorithms: {
          featureTypes: ['SIFT', 'ORB'],
          ransacTypes: ['STANDARD', 'PROSAC'],
        },
      };

      expect(() => ClientConfigSchema.parse(validData)).not.toThrow();
    });
  });

  describe('validateApiResponse', () => {
    it('should return validated data for valid input', () => {
      const validData = {
        status: 'healthy',
        timestamp: '2025-01-01T12:00:00Z',
        version: '1.0.0',
        uptime: 3600,
      };

      const result = validateApiResponse(HealthResponseSchema, validData);
      expect(result).toEqual(validData);
    });

    it('should throw descriptive error for invalid input', () => {
      const invalidData = {
        status: 'invalid-status',
        timestamp: '2025-01-01T12:00:00Z',
        version: '1.0.0',
        uptime: 3600,
      };

      expect(() => validateApiResponse(HealthResponseSchema, invalidData)).toThrow(
        /API response validation failed/
      );
    });
  });

  describe('TaskResponseSchema', () => {
    it('should validate task response with all fields', () => {
      const validData = {
        task_id: 'task-123',
        status: 'running',
        message: 'Processing experiment',
        progress: 0.45,
        current_step: 'Feature extraction',
        total_steps: 10,
        experiment_id: 'exp-123',
        created_at: '2025-01-01T12:00:00Z',
        updated_at: '2025-01-01T12:05:00Z',
        estimated_remaining_time: 300,
      };

      expect(() => TaskResponseSchema.parse(validData)).not.toThrow();
    });

    it('should validate task response with minimal fields', () => {
      const validData = {
        task_id: 'task-123',
        status: 'pending',
        message: 'Task created',
        progress: 0.0,
        created_at: '2025-01-01T12:00:00Z',
        updated_at: '2025-01-01T12:00:00Z',
      };

      expect(() => TaskResponseSchema.parse(validData)).not.toThrow();
    });

    it('should reject invalid progress values', () => {
      const invalidData = {
        task_id: 'task-123',
        status: 'running',
        message: 'Processing',
        progress: 1.5, // Invalid: > 100
        created_at: '2025-01-01T12:00:00Z',
        updated_at: '2025-01-01T12:00:00Z',
      };

      expect(() => TaskResponseSchema.parse(invalidData)).toThrow();
    });
  });
});

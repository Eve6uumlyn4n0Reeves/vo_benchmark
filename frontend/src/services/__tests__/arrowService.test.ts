/**
 * Arrow服务测试
 */

import { arrowService } from '../arrowService';

// Mock fetch
global.fetch = jest.fn();

// Mock Worker
class MockWorker {
  onmessage: ((e: MessageEvent) => void) | null = null;
  onerror: ((e: ErrorEvent) => void) | null = null;
  
  constructor(public url: string) {}
  
  postMessage(data: any, transfer?: Transferable[]) {
    // 模拟异步处理
    setTimeout(() => {
      if (this.onmessage) {
        const response = {
          data: {
            id: data.id,
            success: true,
            result: this.mockParseResult(data.type)
          }
        };
        this.onmessage(response as MessageEvent);
      }
    }, 10);
  }
  
  terminate() {}
  
  private mockParseResult(type: string) {
    if (type === 'parseTrajectory') {
      return {
        estimated_trajectory: [
          { x: 1.0, y: 2.0, z: 3.0, timestamp: 0.1, frame_id: 1 },
          { x: 1.1, y: 2.1, z: 3.1, timestamp: 0.2, frame_id: 2 }
        ],
        groundtruth_trajectory: [],
        reference_trajectory: [],
        metadata: { version: 'ui', points: 2 }
      };
    } else if (type === 'parsePRCurve') {
      return {
        precisions: [0.9, 0.8, 0.7],
        recalls: [0.1, 0.5, 0.9],
        thresholds: [0.9, 0.5, 0.1],
        f1_scores: [0.18, 0.62, 0.78],
        metadata: { auc_score: '0.85' }
      };
    }
    return {};
  }
}

// Mock Worker constructor
(global as any).Worker = MockWorker;

describe('ArrowService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (fetch as jest.Mock).mockClear();
  });

  afterEach(() => {
    arrowService.dispose();
  });

  describe('getManifest', () => {
    it('should fetch manifest successfully', async () => {
      const mockManifest = {
        version: 1,
        experiment_id: 'test_exp',
        algorithm_key: 'test_alg',
        trajectory: {
          ui: {
            url: '/assets/test.ui.arrow',
            bytes: 1000,
            encoding: 'arrow-ipc'
          }
        }
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockManifest)
      });

      const result = await arrowService.getManifest('test_exp', 'test_alg');

      expect(fetch).toHaveBeenCalledWith('/api/v1/results/test_exp/test_alg/manifest');
      expect(result).toEqual(mockManifest);
    });

    it('should handle fetch error', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found'
      });

      await expect(arrowService.getManifest('test_exp', 'test_alg'))
        .rejects.toThrow('获取清单失败: 404 Not Found');
    });

    it('should handle network error', async () => {
      (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      await expect(arrowService.getManifest('test_exp', 'test_alg'))
        .rejects.toThrow('Network error');
    });
  });

  describe('loadTrajectory', () => {
    const mockManifest = {
      trajectory: {
        ui: {
          url: '/assets/test.ui.arrow',
          bytes: 1000,
          encoding: 'arrow-ipc'
        },
        full: {
          url: '/assets/test.arrow',
          bytes: 5000,
          encoding: 'arrow-ipc'
        }
      }
    };

    it('should load UI trajectory via Arrow', async () => {
      // Mock manifest fetch
      (fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockManifest)
        })
        // Mock Arrow file fetch
        .mockResolvedValueOnce({
          ok: true,
          arrayBuffer: () => Promise.resolve(new ArrayBuffer(1000))
        });

      const result = await arrowService.loadTrajectory('test_exp', 'test_alg');

      expect(fetch).toHaveBeenCalledTimes(2);
      expect(fetch).toHaveBeenNthCalledWith(1, '/api/v1/results/test_exp/test_alg/manifest');
      expect(fetch).toHaveBeenNthCalledWith(2, '/assets/test.ui.arrow');
      
      expect(result.estimated_trajectory).toHaveLength(2);
      expect(result.metadata.version).toBe('ui');
    });

    it('should load full trajectory when requested', async () => {
      // Mock manifest fetch
      (fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockManifest)
        })
        // Mock Arrow file fetch
        .mockResolvedValueOnce({
          ok: true,
          arrayBuffer: () => Promise.resolve(new ArrayBuffer(5000))
        });

      const result = await arrowService.loadTrajectory('test_exp', 'test_alg', {
        maxPoints: 'full'
      });

      expect(fetch).toHaveBeenNthCalledWith(2, '/assets/test.arrow');
    });

    it('should fallback to JSON API when Arrow fails', async () => {
      const mockJsonTrajectory = {
        estimated_trajectory: [
          { x: 1.0, y: 2.0, z: 3.0, timestamp: 0.1, frame_id: 1 }
        ]
      };

      // Mock manifest fetch failure
      (fetch as jest.Mock)
        .mockRejectedValueOnce(new Error('Manifest not found'))
        // Mock JSON API success
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockJsonTrajectory)
        });

      const result = await arrowService.loadTrajectory('test_exp', 'test_alg');

      expect(fetch).toHaveBeenCalledWith('/api/v1/results/test_exp/test_alg/trajectory?');
      expect(result).toEqual(mockJsonTrajectory);
    });

    it('should include reference trajectory when requested', async () => {
      const mockJsonTrajectory = {
        estimated_trajectory: [
          { x: 1.0, y: 2.0, z: 3.0, timestamp: 0.1, frame_id: 1 }
        ],
        reference_trajectory: [
          { x: 0.9, y: 1.9, z: 2.9, timestamp: 0.1 }
        ]
      };

      (fetch as jest.Mock)
        .mockRejectedValueOnce(new Error('Arrow not available'))
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockJsonTrajectory)
        });

      const result = await arrowService.loadTrajectory('test_exp', 'test_alg', {
        includeReference: true
      });

      expect(fetch).toHaveBeenCalledWith('/api/v1/results/test_exp/test_alg/trajectory?include_reference=true');
      expect(result.reference_trajectory).toBeDefined();
    });

    it('should remove reference trajectory when not requested', async () => {
      // Mock manifest and Arrow loading
      (fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockManifest)
        })
        .mockResolvedValueOnce({
          ok: true,
          arrayBuffer: () => Promise.resolve(new ArrayBuffer(1000))
        });

      const result = await arrowService.loadTrajectory('test_exp', 'test_alg', {
        includeReference: false
      });

      expect(result.reference_trajectory).toBeUndefined();
    });
  });

  describe('loadPRCurve', () => {
    const mockManifest = {
      pr_curve: {
        ui: {
          url: '/assets/test.ui.arrow',
          bytes: 500,
          encoding: 'arrow-ipc'
        }
      }
    };

    it('should load PR curve via Arrow', async () => {
      (fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockManifest)
        })
        .mockResolvedValueOnce({
          ok: true,
          arrayBuffer: () => Promise.resolve(new ArrayBuffer(500))
        });

      const result = await arrowService.loadPRCurve('test_exp', 'test_alg');

      expect(fetch).toHaveBeenCalledTimes(2);
      expect(result.precisions).toEqual([0.9, 0.8, 0.7]);
      expect(result.recalls).toEqual([0.1, 0.5, 0.9]);
    });

    it('should fallback to JSON API', async () => {
      const mockJsonPR = {
        precisions: [0.9, 0.8],
        recalls: [0.1, 0.5],
        thresholds: [0.9, 0.5],
        auc_score: 0.75
      };

      (fetch as jest.Mock)
        .mockRejectedValueOnce(new Error('Arrow not available'))
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockJsonPR)
        });

      const result = await arrowService.loadPRCurve('test_exp', 'test_alg');

      expect(fetch).toHaveBeenCalledWith('/api/v1/results/test_exp/test_alg/pr-curve');
      expect(result).toEqual(mockJsonPR);
    });
  });

  describe('Worker management', () => {
    it('should initialize worker on first use', async () => {
      const mockManifest = {
        trajectory: {
          ui: {
            url: '/assets/test.ui.arrow',
            bytes: 1000,
            encoding: 'arrow-ipc'
          }
        }
      };

      (fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockManifest)
        })
        .mockResolvedValueOnce({
          ok: true,
          arrayBuffer: () => Promise.resolve(new ArrayBuffer(1000))
        });

      await arrowService.loadTrajectory('test_exp', 'test_alg');

      // Worker should be initialized
      expect((arrowService as any).worker).toBeDefined();
    });

    it('should dispose worker properly', () => {
      // Initialize worker
      (arrowService as any).initWorker();
      
      const worker = (arrowService as any).worker;
      expect(worker).toBeDefined();

      // Dispose
      arrowService.dispose();

      expect((arrowService as any).worker).toBeNull();
    });

    it('should handle worker errors', async () => {
      // Mock worker that throws error
      class ErrorWorker extends MockWorker {
        postMessage() {
          setTimeout(() => {
            if (this.onerror) {
              this.onerror(new ErrorEvent('error', { message: 'Worker error' }));
            }
          }, 10);
        }
      }

      (global as any).Worker = ErrorWorker;

      const mockManifest = {
        trajectory: {
          ui: {
            url: '/assets/test.ui.arrow',
            bytes: 1000,
            encoding: 'arrow-ipc'
          }
        }
      };

      (fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockManifest)
        })
        .mockResolvedValueOnce({
          ok: true,
          arrayBuffer: () => Promise.resolve(new ArrayBuffer(1000))
        });

      // Should fallback to JSON when worker fails
      await expect(arrowService.loadTrajectory('test_exp', 'test_alg'))
        .rejects.toThrow();
    });
  });

  describe('Performance monitoring integration', () => {
    it('should measure performance for all operations', async () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();

      const mockManifest = { trajectory: {} };
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockManifest)
      });

      await arrowService.getManifest('test_exp', 'test_alg');

      // Should have performance logs
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('[Performance] getManifest-test_alg:')
      );

      consoleSpy.mockRestore();
    });
  });
});

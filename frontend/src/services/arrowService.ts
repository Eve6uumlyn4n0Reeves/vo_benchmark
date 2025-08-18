/**
 * Arrow数据服务
 * 提供高效的Arrow格式数据加载和解析
 */

import { performanceMonitor } from '@/utils/performance';

interface ArrowWorkerMessage {
  id: string;
  type: 'parseTrajectory' | 'parsePRCurve';
  data: ArrayBuffer;
}

interface ArrowWorkerResponse {
  id: string;
  success: boolean;
  result?: any;
  error?: {
    message: string;
    stack?: string;
  };
}

class ArrowService {
  private worker: Worker | null = null;
  private pendingRequests = new Map<string, {
    resolve: (value: any) => void;
    reject: (error: Error) => void;
  }>();
  private requestIdCounter = 0;

  /**
   * 初始化Worker
   */
  private async initWorker(): Promise<Worker> {
    if (this.worker) return this.worker;

    try {
      // Use module worker bundled with Vite (local dependency, no CDN)
      this.worker = new Worker(new URL('../workers/arrowParser.worker.ts', import.meta.url), { type: 'module' });

      this.worker.onmessage = (e: MessageEvent<ArrowWorkerResponse>) => {
        const { id, success, result, error } = e.data;
        const request = this.pendingRequests.get(id);
        
        if (request) {
          this.pendingRequests.delete(id);
          
          if (success) {
            request.resolve(result);
          } else {
            request.reject(new Error(error?.message || 'Worker解析失败'));
          }
        }
      };

      this.worker.onerror = (error) => {
        console.error('Arrow Worker错误:', error);
        // 清理所有待处理的请求
        for (const [, request] of this.pendingRequests) {
          request.reject(new Error('Worker错误'));
        }
        this.pendingRequests.clear();
      };

      return this.worker;
    } catch (error) {
      console.error('初始化Arrow Worker失败:', error);
      throw error;
    }
  }

  /**
   * 发送解析请求到Worker
   */
  private async sendToWorker(type: 'parseTrajectory' | 'parsePRCurve', data: ArrayBuffer): Promise<any> {
    const worker = await this.initWorker();
    const id = `req_${++this.requestIdCounter}`;

    return new Promise((resolve, reject) => {
      this.pendingRequests.set(id, { resolve, reject });
      
      const message: ArrowWorkerMessage = { id, type, data };
      worker.postMessage(message, [data]); // 转移ArrayBuffer所有权
      
      // 设置超时
      setTimeout(() => {
        if (this.pendingRequests.has(id)) {
          this.pendingRequests.delete(id);
          reject(new Error('Worker解析超时'));
        }
      }, 30000); // 30秒超时
    });
  }

  /**
   * 获取Manifest清单
   */
  async getManifest(experimentId: string, algorithmKey: string): Promise<any> {
    return performanceMonitor.measure(
      `getManifest-${algorithmKey}`,
      async () => {
        const response = await fetch(`/api/v1/results/${experimentId}/${algorithmKey}/manifest`);
        
        if (!response.ok) {
          throw new Error(`获取清单失败: ${response.status} ${response.statusText}`);
        }
        
        const manifest = await response.json();
        console.log(`[ArrowService] 清单获取成功:`, manifest);
        
        return manifest;
      },
      { experimentId, algorithmKey }
    );
  }

  /**
   * 加载轨迹数据
   */
  async loadTrajectory(
    experimentId: string, 
    algorithmKey: string, 
    options: {
      maxPoints?: number | 'full';
      includeReference?: boolean;
      preferArrow?: boolean;
    } = {}
  ): Promise<any> {
    const { maxPoints = 1500, includeReference = false, preferArrow = true } = options;

    return performanceMonitor.measure(
      `loadTrajectory-${algorithmKey}`,
      async () => {
        if (preferArrow) {
          try {
            // 首先尝试获取清单
            const manifest = await this.getManifest(experimentId, algorithmKey);
            
            // 选择合适的轨迹版本
            const trajectory = manifest.trajectory;
            let assetUrl: string | null = null;
            
            if (maxPoints === 'full' && trajectory.full) {
              assetUrl = trajectory.full.url;
            } else if (trajectory.ui) {
              assetUrl = trajectory.ui.url;
            }
            
            if (assetUrl) {
              console.log(`[ArrowService] 加载Arrow轨迹: ${assetUrl}`);
              
              // 下载Arrow文件
              const response = await fetch(assetUrl);
              if (!response.ok) {
                throw new Error(`下载Arrow文件失败: ${response.status}`);
              }
              
              const arrayBuffer = await response.arrayBuffer();
              console.log(`[ArrowService] Arrow文件下载完成: ${arrayBuffer.byteLength} bytes`);
              
              // 在Worker中解析
              const result = await this.sendToWorker('parseTrajectory', arrayBuffer);
              
              // 如果不包含参考轨迹，移除它
              if (!includeReference) {
                delete result.reference_trajectory;
              }
              
              console.log(`[ArrowService] Arrow轨迹解析完成: ${result.estimated_trajectory?.length || 0} 点`);
              return result;
            }
          } catch (error) {
            console.warn(`[ArrowService] Arrow轨迹加载失败，回退到JSON:`, error);
          }
        }
        
        // 回退到传统JSON API
        const params = new URLSearchParams();
        if (maxPoints !== 1500) params.set('max_points', String(maxPoints));
        if (includeReference) params.set('include_reference', 'true');
        
        const url = `/api/v1/results/${experimentId}/${algorithmKey}/trajectory?${params}`;
        const response = await fetch(url);
        
        if (!response.ok) {
          throw new Error(`获取轨迹失败: ${response.status} ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log(`[ArrowService] JSON轨迹加载完成: ${result.estimated_trajectory?.length || 0} 点`);
        
        return result;
      },
      { experimentId, algorithmKey, maxPoints, includeReference }
    );
  }

  /**
   * 加载PR曲线数据
   */
  async loadPRCurve(
    experimentId: string, 
    algorithmKey: string,
    options: {
      maxPoints?: number | 'full';
      preferArrow?: boolean;
    } = {}
  ): Promise<any> {
    const { maxPoints = 500, preferArrow = true } = options;

    return performanceMonitor.measure(
      `loadPRCurve-${algorithmKey}`,
      async () => {
        if (preferArrow) {
          try {
            // 获取清单
            const manifest = await this.getManifest(experimentId, algorithmKey);
            
            // 选择合适的PR曲线版本
            const prCurve = manifest.pr_curve;
            let assetUrl: string | null = null;
            
            if (maxPoints === 'full' && prCurve.full) {
              assetUrl = prCurve.full.url;
            } else if (prCurve.ui) {
              assetUrl = prCurve.ui.url;
            }
            
            if (assetUrl) {
              console.log(`[ArrowService] 加载Arrow PR曲线: ${assetUrl}`);
              
              // 下载Arrow文件
              const response = await fetch(assetUrl);
              if (!response.ok) {
                throw new Error(`下载Arrow文件失败: ${response.status}`);
              }
              
              const arrayBuffer = await response.arrayBuffer();
              console.log(`[ArrowService] Arrow文件下载完成: ${arrayBuffer.byteLength} bytes`);
              
              // 在Worker中解析
              const result = await this.sendToWorker('parsePRCurve', arrayBuffer);
              
              console.log(`[ArrowService] Arrow PR曲线解析完成: ${result.precisions?.length || 0} 点`);
              return result;
            }
          } catch (error) {
            console.warn(`[ArrowService] Arrow PR曲线加载失败，回退到JSON:`, error);
          }
        }
        
        // 回退到传统JSON API
        const url = `/api/v1/results/${experimentId}/${algorithmKey}/pr-curve`;
        const response = await fetch(url);
        
        if (!response.ok) {
          throw new Error(`获取PR曲线失败: ${response.status} ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log(`[ArrowService] JSON PR曲线加载完成: ${result.precisions?.length || 0} 点`);
        
        return result;
      },
      { experimentId, algorithmKey, maxPoints }
    );
  }

  /**
   * 清理资源
   */
  dispose(): void {
    if (this.worker) {
      this.worker.terminate();
      this.worker = null;
    }
    
    // 拒绝所有待处理的请求
    for (const [, request] of this.pendingRequests) {
      request.reject(new Error('ArrowService已销毁'));
    }
    this.pendingRequests.clear();
  }
}

// 全局实例
export const arrowService = new ArrowService();

// 清理函数（在页面卸载时调用）
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    arrowService.dispose();
  });
}

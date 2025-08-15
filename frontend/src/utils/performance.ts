import React from 'react';

/**
 * 性能监控工具
 * 用于测量和记录各种操作的性能指标
 */

interface PerformanceMetric {
  name: string;
  startTime: number;
  endTime?: number;
  duration?: number;
  metadata?: Record<string, any>;
}

class PerformanceMonitor {
  private metrics: Map<string, PerformanceMetric> = new Map();
  private enabled: boolean = import.meta.env.DEV;

  /**
   * 开始测量
   */
  start(name: string, metadata?: Record<string, any>): void {
    if (!this.enabled) return;
    
    this.metrics.set(name, {
      name,
      startTime: performance.now(),
      metadata,
    });
  }

  /**
   * 结束测量并记录
   */
  end(name: string, additionalMetadata?: Record<string, any>): number | null {
    if (!this.enabled) return null;
    
    const metric = this.metrics.get(name);
    if (!metric) {
      console.warn(`[PerformanceMonitor] 未找到测量项: ${name}`);
      return null;
    }

    const endTime = performance.now();
    const duration = endTime - metric.startTime;
    
    metric.endTime = endTime;
    metric.duration = duration;
    
    if (additionalMetadata) {
      metric.metadata = { ...metric.metadata, ...additionalMetadata };
    }

    // 记录到控制台
    const metadataStr = metric.metadata ? 
      ` (${Object.entries(metric.metadata).map(([k, v]) => `${k}: ${v}`).join(', ')})` : '';
    console.log(`[Performance] ${name}: ${duration.toFixed(2)}ms${metadataStr}`);

    return duration;
  }

  /**
   * 测量异步操作
   */
  async measure<T>(name: string, operation: () => Promise<T>, metadata?: Record<string, any>): Promise<T> {
    this.start(name, metadata);
    try {
      const result = await operation();
      this.end(name);
      return result;
    } catch (error) {
      this.end(name, { error: error instanceof Error ? error.message : 'Unknown error' });
      throw error;
    }
  }

  /**
   * 测量同步操作
   */
  measureSync<T>(name: string, operation: () => T, metadata?: Record<string, any>): T {
    this.start(name, metadata);
    try {
      const result = operation();
      this.end(name);
      return result;
    } catch (error) {
      this.end(name, { error: error instanceof Error ? error.message : 'Unknown error' });
      throw error;
    }
  }

  /**
   * 获取所有指标
   */
  getMetrics(): PerformanceMetric[] {
    return Array.from(this.metrics.values());
  }

  /**
   * 清除所有指标
   */
  clear(): void {
    this.metrics.clear();
  }

  /**
   * 启用/禁用监控
   */
  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
  }
}

// 全局实例
export const performanceMonitor = new PerformanceMonitor();

/**
 * 装饰器：自动测量方法执行时间
 */
export function measurePerformance(name?: string) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value;
    const metricName = name || `${target.constructor.name}.${propertyKey}`;

    descriptor.value = function (...args: any[]) {
      return performanceMonitor.measureSync(metricName, () => originalMethod.apply(this, args));
    };

    return descriptor;
  };
}

/**
 * Hook：测量React组件渲染性能
 */
export function usePerformanceMonitor(componentName: string) {
  React.useEffect(() => {
    performanceMonitor.start(`${componentName}.mount`);
    return () => {
      performanceMonitor.end(`${componentName}.mount`);
    };
  }, [componentName]);

  const measureRender = React.useCallback((renderName: string = 'render') => {
    performanceMonitor.start(`${componentName}.${renderName}`);
    return () => performanceMonitor.end(`${componentName}.${renderName}`);
  }, [componentName]);

  return { measureRender };
}

/**
 * 测量网络请求性能
 */
export async function measureNetworkRequest<T>(
  name: string,
  request: () => Promise<T>,
  metadata?: Record<string, any>
): Promise<T> {
  const startTime = performance.now();
  
  try {
    const result = await request();
    const duration = performance.now() - startTime;
    
    console.log(`[Network] ${name}: ${duration.toFixed(2)}ms`, metadata);
    
    return result;
  } catch (error) {
    const duration = performance.now() - startTime;
    console.error(`[Network] ${name} 失败: ${duration.toFixed(2)}ms`, error, metadata);
    throw error;
  }
}

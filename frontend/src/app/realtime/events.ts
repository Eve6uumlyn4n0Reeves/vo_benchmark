/**
 * SSE 事件常量与类型定义
 * 统一管理实时事件的名称和数据结构
 */

// 事件名称常量
export const TASK_UPDATED = 'task_updated' as const;
export const TASK_LOG = 'task_log' as const;
export const HEARTBEAT = 'heartbeat' as const;

// 事件类型联合
export type EventType = typeof TASK_UPDATED | typeof TASK_LOG | typeof HEARTBEAT;

// 基础事件结构
export interface BaseRealtimeEvent {
  type: EventType;
  data: unknown;
}

// 任务更新事件
export interface TaskUpdatedEvent extends BaseRealtimeEvent {
  type: typeof TASK_UPDATED;
  data: {
    task_id: string;
    status: string;
    progress?: number;
    message?: string;
    current_step?: number | string;
    total_steps?: number;
    error_details?: string;
    estimated_remaining_time?: number;
    [key: string]: unknown;
  };
}

// 任务日志事件
export interface TaskLogEvent extends BaseRealtimeEvent {
  type: typeof TASK_LOG;
  data: {
    task_id: string;
    // 后端当前字段为 `line`；保留对 `log_entry` 的兼容
    line?: string;
    log_entry?: string;
    timestamp?: string;
    level?: string;
    [key: string]: unknown;
  };
}

// 心跳事件
export interface HeartbeatEvent extends BaseRealtimeEvent {
  type: typeof HEARTBEAT;
  data: {
    ts: number;
    [key: string]: unknown;
  };
}

// 所有事件类型的联合
export type RealtimeEvent = TaskUpdatedEvent | TaskLogEvent | HeartbeatEvent;

// 事件处理器类型
export type EventHandler<T extends RealtimeEvent = RealtimeEvent> = (event: T) => void;

// 事件名称到事件类型的映射
export type EventTypeMap = {
  [TASK_UPDATED]: TaskUpdatedEvent;
  [TASK_LOG]: TaskLogEvent;
  [HEARTBEAT]: HeartbeatEvent;
};

/**
 * 类型守卫：检查是否为任务更新事件
 */
export function isTaskUpdatedEvent(event: RealtimeEvent): event is TaskUpdatedEvent {
  return event.type === TASK_UPDATED;
}

/**
 * 类型守卫：检查是否为任务日志事件
 */
export function isTaskLogEvent(event: RealtimeEvent): event is TaskLogEvent {
  return event.type === TASK_LOG;
}

/**
 * 类型守卫：检查是否为心跳事件
 */
export function isHeartbeatEvent(event: RealtimeEvent): event is HeartbeatEvent {
  return event.type === HEARTBEAT;
}

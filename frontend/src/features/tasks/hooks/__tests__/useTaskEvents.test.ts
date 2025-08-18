import { renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as React from 'react';
import { useTaskEvents } from '../useTaskEvents';
import { TASK_UPDATED, type TaskUpdatedEvent } from '@/app/realtime/events';

// Mock the realtime provider
const mockSubscribe = jest.fn();
const mockIsConnected = true;

jest.mock('@/app/realtime/RealtimeProvider', () => ({
  useRealtime: () => ({
    isConnected: mockIsConnected,
    subscribe: mockSubscribe,
  }),
}));

// Mock query keys
jest.mock('@/api/queryKeys', () => ({
  queryKeys: {
    tasks: ['tasks'],
    tasksDetail: (id: string) => ['tasks', id],
  },
}));

describe('useTaskEvents', () => {
  let queryClient: QueryClient;
  let wrapper: React.FC<{ children: React.ReactNode }>;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    wrapper = ({ children }) =>
      React.createElement(QueryClientProvider, { client: queryClient }, children);

    mockSubscribe.mockClear();
  });

  afterEach(() => {
    queryClient.clear();
  });

  it('subscribes to realtime events when enabled', () => {
    const mockUnsubscribe = jest.fn();
    mockSubscribe.mockReturnValue(mockUnsubscribe);

    const { unmount } = renderHook(() => useTaskEvents(true), { wrapper });

    expect(mockSubscribe).toHaveBeenCalledTimes(1);
    expect(mockSubscribe).toHaveBeenCalledWith(expect.any(Function));

    unmount();
    expect(mockUnsubscribe).toHaveBeenCalledTimes(1);
  });

  it('does not subscribe when disabled', () => {
    renderHook(() => useTaskEvents(false), { wrapper });

    expect(mockSubscribe).not.toHaveBeenCalled();
  });

  it('updates query cache on task_updated event', () => {
    const mockUnsubscribe = jest.fn();
    mockSubscribe.mockReturnValue(mockUnsubscribe);

    // Pre-populate cache with task data
    const taskId = 'test-task-123';
    const initialTask = {
      task_id: taskId,
      status: 'pending',
      progress: 0.0,
      message: 'Starting...',
    };

    queryClient.setQueryData(['tasks', taskId], initialTask);

    renderHook(() => useTaskEvents(true), { wrapper });

    // Get the handler that was passed to subscribe
    const handler = mockSubscribe.mock.calls[0][0];

    // Simulate a task_updated event
    const updateEvent: TaskUpdatedEvent = {
      type: TASK_UPDATED,
      data: {
        task_id: taskId,
        status: 'running',
        progress: 0.5,
        message: 'Processing...',
      },
    };

    handler(updateEvent);

    // Check that the cache was updated
    const updatedTask = queryClient.getQueryData(['tasks', taskId]);
    expect(updatedTask).toEqual({
      task_id: taskId,
      status: 'running',
      progress: 0.5,
      message: 'Processing...',
    });
  });

  it('ignores non-task_updated events', () => {
    const mockUnsubscribe = jest.fn();
    mockSubscribe.mockReturnValue(mockUnsubscribe);

    const taskId = 'test-task-123';
    const initialTask = {
      task_id: taskId,
      status: 'pending',
      progress: 0.0,
      message: 'Starting...',
    };

    queryClient.setQueryData(['tasks', taskId], initialTask);

    renderHook(() => useTaskEvents(true), { wrapper });

    const handler = mockSubscribe.mock.calls[0][0];

    // Simulate a different event type
    const logEvent = {
      type: 'task_log',
      data: {
        task_id: taskId,
        log_entry: 'Some log message',
      },
    };

    handler(logEvent);

    // Check that the cache was not updated
    const unchangedTask = queryClient.getQueryData(['tasks', taskId]);
    expect(unchangedTask).toEqual(initialTask);
  });

  it('returns connection status', () => {
    const mockUnsubscribe = jest.fn();
    mockSubscribe.mockReturnValue(mockUnsubscribe);

    const { result } = renderHook(() => useTaskEvents(true), { wrapper });

    expect(result.current.isConnected).toBe(true);
  });
});

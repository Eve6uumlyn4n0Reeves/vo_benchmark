import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useRealtime } from '@/app/realtime/RealtimeProvider';
import { queryKeys } from '@/api/queryKeys';

interface TaskUpdatedEventData {
  task_id: string;
  status?: string;
  progress?: number;
  message?: string;
  experiment_id?: string;
}

export const useTaskEvents = (enabled: boolean = true) => {
  const queryClient = useQueryClient();

  const { isConnected, subscribe } = useRealtime();

  useEffect(() => {
    if (!enabled) return;

    const handler = (msg: any) => {
      if (msg.type === 'task_updated') {
        const data = msg.data as TaskUpdatedEventData;
        const { task_id, status, progress, message } = data;

        if (task_id) {
          queryClient.setQueryData(queryKeys.tasksDetail(task_id), (old: any) => {
            if (!old) return old;
            return {
              ...old,
              status: status ?? old.status,
              progress: typeof progress === 'number' ? progress : old.progress,
              message: message ?? old.message,
            };
          });
        }
        // 轻量刷新：列表做一次节流失效
        queryClient.invalidateQueries({ queryKey: queryKeys.tasks });
      }
    };

    const unsubscribe = subscribe(handler);
    return () => unsubscribe();
  }, [enabled, subscribe, queryClient]);

  useEffect(() => {
    // Could toggle polling off when connected, but keep current behavior for now
  }, [isConnected]);

  return { isConnected };
};

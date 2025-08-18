import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useRealtime, type RealtimeMessage } from '@/app/realtime/RealtimeProvider';
import { queryKeys } from '@/api/queryKeys';
import { isTaskUpdatedEvent } from '@/app/realtime/events';

export const useTaskEvents = (enabled: boolean = true) => {
  const queryClient = useQueryClient();

  const { isConnected, subscribe } = useRealtime();

  useEffect(() => {
    if (!enabled) return;

    const handler = (msg: RealtimeMessage) => {
      if (isTaskUpdatedEvent(msg as any)) {
        const data = (msg as any).data as any;
        const { task_id, status, progress, message, experiment_id } = data || {};

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
        // 若任务关联了实验，同步失效实验与结果概览缓存，确保跨页面一致
        if (experiment_id) {
          queryClient.invalidateQueries({ queryKey: queryKeys.experiments });
          queryClient.invalidateQueries({ queryKey: queryKeys.experimentsDetail(experiment_id) });
          queryClient.invalidateQueries({ queryKey: queryKeys.resultsOverview(experiment_id) });
        }
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

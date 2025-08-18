import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useRealtime, type RealtimeMessage } from '@/app/realtime/RealtimeProvider';
import { queryKeys } from '@/api/queryKeys';

const isExpEvent = (msg: RealtimeMessage, types: string[]) => types.includes(msg.type);

export const useExperimentEvents = (enabled: boolean = true) => {
  const queryClient = useQueryClient();
  const { subscribe } = useRealtime();

  useEffect(() => {
    if (!enabled) return;

    const handler = (msg: RealtimeMessage) => {
      if (isExpEvent(msg, ['experiment_started','experiment_progress','experiment_completed','experiment_failed','experiment_deleted'])) {
        const data: any = msg.data || {};
        const experimentId = data.experiment_id;

        // 更新详情缓存
        if (experimentId) {
          queryClient.invalidateQueries({ queryKey: queryKeys.experiments });
          queryClient.invalidateQueries({ queryKey: queryKeys.experimentsDetail(experimentId) });
          queryClient.invalidateQueries({ queryKey: queryKeys.experimentsHistory(experimentId) });
          queryClient.invalidateQueries({ queryKey: queryKeys.resultsOverview(experimentId) });
        } else {
          // 无 experimentId 时至少刷新列表
          queryClient.invalidateQueries({ queryKey: queryKeys.experiments });
        }
      }
    };

    const unsubscribe = subscribe(handler);
    return () => unsubscribe();
  }, [enabled, subscribe, queryClient]);
};


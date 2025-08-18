import { useRef, useEffect } from 'react';
import { useSSE, type SSEMessage } from '@/hooks/useSSE';
import { isTaskLogEvent } from '@/app/realtime/events';

export const useTaskLogsEvents = (taskId: string | undefined, enabled: boolean, onLogLine: (line: string) => void) => {
  const bufferRef = useRef<string[]>([]);

  const flush = () => {
    if (bufferRef.current.length > 0) {
      const lines = bufferRef.current.splice(0, bufferRef.current.length);
      lines.forEach(onLogLine);
    }
  };

  const { isConnected } = useSSE('/api/v1/events/', {
    enabled: !!taskId && enabled,
    onMessage: (msg: SSEMessage) => {
      if (isTaskLogEvent(msg as any)) {
        const data = (msg as any).data as { task_id: string; line?: string; log_entry?: string };
        const { task_id, line, log_entry } = data;
        const text = line ?? log_entry;
        if (task_id === taskId && text) {
          bufferRef.current.push(text);
        }
      }
    },
  });

  useEffect(() => {
    const t = setInterval(flush, 500);
    return () => clearInterval(t);
  }, []);

  return { isConnected };
};

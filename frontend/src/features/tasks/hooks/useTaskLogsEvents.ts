import { useRef, useEffect } from 'react';
import { useSSE } from '@/hooks/useSSE';

interface TaskLogEventData {
  task_id: string;
  line?: string;
}

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
    onMessage: (msg) => {
      if (msg.type === 'task_log') {
        const data = msg.data as TaskLogEventData;
        if (data.task_id === taskId && data.line) {
          bufferRef.current.push(data.line);
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

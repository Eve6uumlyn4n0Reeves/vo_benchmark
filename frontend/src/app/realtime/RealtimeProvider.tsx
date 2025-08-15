import React, { createContext, useContext, useMemo, useCallback } from 'react';
import { useSSE } from '@/hooks/useSSE';

export type RealtimeMessage = {
  type: string;
  data: unknown;
  timestamp: number;
};

type RealtimeContextValue = {
  isConnected: boolean;
  lastMessage: RealtimeMessage | null;
  subscribe: (handler: (msg: RealtimeMessage) => void) => () => void;
};

const RealtimeContext = createContext<RealtimeContextValue | null>(null);

export const RealtimeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Maintain a single SSE connection
  const subscribersRef = React.useRef(new Set<(msg: RealtimeMessage) => void>());

  const onMessage = useCallback((msg: any) => {
    // fan-out to subscribers
    subscribersRef.current.forEach(h => {
      try { h(msg); } catch {}
    });
  }, []);

  const { isConnected, lastMessage } = useSSE('/api/v1/events/', {
    enabled: true,
    onMessage,
  });

  const subscribe = useCallback((handler: (msg: RealtimeMessage) => void) => {
    subscribersRef.current.add(handler);
    return () => subscribersRef.current.delete(handler);
  }, []);

  const value = useMemo<RealtimeContextValue>(() => ({ isConnected, lastMessage: lastMessage as any, subscribe }), [isConnected, lastMessage, subscribe]);

  return (
    <RealtimeContext.Provider value={value}>{children}</RealtimeContext.Provider>
  );
};

export const useRealtime = () => {
  const ctx = useContext(RealtimeContext);
  if (!ctx) throw new Error('useRealtime must be used within RealtimeProvider');
  return ctx;
};


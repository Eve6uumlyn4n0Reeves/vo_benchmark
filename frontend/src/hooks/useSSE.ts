import { useEffect, useRef, useState, useCallback } from 'react';
import { env } from '@/utils/env';

export interface SSEMessage {
  type: string;
  data: unknown;
  timestamp: number;
}

export interface SSEState {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  lastMessage: SSEMessage | null;
  reconnectAttempts: number;
}

export interface SSEControls {
  connect: () => void;
  disconnect: () => void;
  reconnect: () => void;
}

export interface UseSSEOptions {
  enabled?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  onMessage?: (message: SSEMessage) => void;
  onError?: (error: Event) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

/**
 * Hook for Server-Sent Events (SSE) connection
 * Handles automatic reconnection with exponential backoff
 * Used for real-time task/experiment status updates
 */
export const useSSE = (url: string, options: UseSSEOptions = {}) => {
  const {
    enabled = true,
    reconnectInterval = env.sseReconnectInterval(),
    maxReconnectAttempts = env.sseMaxReconnectAttempts(),
    onMessage,
    onError,
    onConnect,
    onDisconnect,
  } = options;

  const [state, setState] = useState<SSEState>({
    isConnected: false,
    isConnecting: false,
    error: null,
    lastMessage: null,
    reconnectAttempts: 0,
  });

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnectRef = useRef(true);
  const reconnectAttemptsRef = useRef(0);

  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;
    clearReconnectTimeout();

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    setState(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
      error: null,
    }));

    onDisconnect?.();
  }, [clearReconnectTimeout, onDisconnect]);

  const connect = useCallback(() => {
    if (!enabled || eventSourceRef.current) {
      return;
    }

    setState(prev => ({ ...prev, isConnecting: true, error: null }));
    shouldReconnectRef.current = true;

    try {
      const eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        reconnectAttemptsRef.current = 0;
        setState(prev => ({
          ...prev,
          isConnected: true,
          isConnecting: false,
          error: null,
          reconnectAttempts: 0,
        }));
        onConnect?.();
      };

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const message: SSEMessage = {
            type: event.type || 'message',
            data,
            timestamp: Date.now(),
          };

          setState(prev => ({ ...prev, lastMessage: message }));
          onMessage?.(message);
        } catch (error) {
          console.error('Failed to parse SSE message:', error);
        }
      };

      eventSource.onerror = (error) => {
        console.error('SSE connection error:', error);
        
        setState(prev => ({
          ...prev,
          isConnected: false,
          isConnecting: false,
          error: 'Connection error',
        }));

        onError?.(error);

        // Close the current connection
        eventSource.close();
        eventSourceRef.current = null;

        // Attempt to reconnect if enabled and within retry limits
        if (shouldReconnectRef.current && reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = Math.min(
            reconnectInterval * Math.pow(2, reconnectAttemptsRef.current),
            30000 // Max 30 seconds
          );

          reconnectAttemptsRef.current += 1;
          setState(prev => ({
            ...prev,
            reconnectAttempts: reconnectAttemptsRef.current,
          }));

          reconnectTimeoutRef.current = setTimeout(() => {
            if (shouldReconnectRef.current) {
              connect();
            }
          }, delay);
        }
      };
    } catch (error) {
      console.error('Failed to create SSE connection:', error);
      setState(prev => ({
        ...prev,
        isConnecting: false,
        error: 'Failed to create connection',
      }));
    }
  }, [enabled, url, onConnect, onMessage, onError, maxReconnectAttempts, reconnectInterval]);

  const reconnect = useCallback(() => {
    disconnect();
    reconnectAttemptsRef.current = 0;
    setState(prev => ({ ...prev, reconnectAttempts: 0 }));
    setTimeout(connect, 100); // Small delay before reconnecting
  }, [disconnect, connect]);

  // Auto-connect when enabled
  useEffect(() => {
    if (enabled) {
      connect();
    } else {
      disconnect();
    }

    return disconnect;
  }, [enabled, connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      shouldReconnectRef.current = false;
      disconnect();
    };
  }, [disconnect]);

  return {
    ...state,
    connect,
    disconnect,
    reconnect,
  };
};

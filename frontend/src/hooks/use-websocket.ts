import { useEffect, useRef, useState, useCallback } from "react";
import { useAuthStore } from "@/stores";

interface UseWebSocketOptions {
  url: string;
  onMessage?: (data: any) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  /** Maximum number of reconnection attempts (0 = infinite) */
  maxReconnectAttempts?: number;
  /** Base delay in ms for exponential backoff */
  reconnectBaseDelay?: number;
  /** Maximum delay in ms between reconnection attempts */
  maxReconnectDelay?: number;
  /** Enable reconnection on connection loss */
  enableReconnect?: boolean;
}

interface WebSocketState {
  isConnected: boolean;
  isConnecting: boolean;
  reconnectAttempts: number;
}

export function useWebSocket({
  url,
  onMessage,
  onConnect,
  onDisconnect,
  onError,
  maxReconnectAttempts = 0, // 0 = infinite
  reconnectBaseDelay = 1000,
  maxReconnectDelay = 30000,
  enableReconnect = true,
}: UseWebSocketOptions) {
  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    reconnectAttempts: 0,
  });

  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const intentionalClose = useRef(false);
  const wasConnected = useRef(false);
  // Track reconnect attempts in a ref to avoid re-creating `connect` on each attempt
  const reconnectAttemptsRef = useRef(0);

  // Get auth state from store
  const { accessToken, isAuthenticated } = useAuthStore();

  // Cleanup function for reconnection timeout
  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeout.current !== null) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    // Don't connect if already connected or connecting
    if (ws.current?.readyState === WebSocket.OPEN ||
        ws.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    // Don't connect if not authenticated
    if (!accessToken) {
      return;
    }

    clearReconnectTimeout();
    intentionalClose.current = false;
    setState(prev => ({ ...prev, isConnecting: true }));

    // Connect without token in URL; token is sent as first message after open
    const wsUrl = url;

    try {
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        // Send authentication token as first message (backend expects this)
        ws.current?.send(JSON.stringify({ token: accessToken }));
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          // Handle ping/pong for connection keepalive
          if (data.type === "ping") {
            ws.current?.send(JSON.stringify({ type: "pong" }));
            return;
          }

          // Backend sends a "connected" confirmation after successful auth;
          // only mark the connection as live once we receive it.
          if (data.type === "connected") {
            wasConnected.current = true;
            reconnectAttemptsRef.current = 0;
            setState({
              isConnected: true,
              isConnecting: false,
              reconnectAttempts: 0,
            });
            onConnect?.();
            return;
          }

          onMessage?.(data);
        } catch (err) {
          console.error("Failed to parse WebSocket message:", err);
          onMessage?.(event.data);
        }
      };

      ws.current.onclose = (event) => {
        setState(prev => ({
          ...prev,
          isConnected: false,
          isConnecting: false,
        }));

        onDisconnect?.();

        // Don't reconnect if:
        // 1. Close was intentional
        // 2. Reconnect is disabled
        // 3. Max attempts reached (if set)
        if (intentionalClose.current || !enableReconnect) {
          return;
        }

        const currentAttempt = reconnectAttemptsRef.current;
        if (maxReconnectAttempts > 0 && currentAttempt >= maxReconnectAttempts) {
          console.error(`WebSocket max reconnection attempts (${maxReconnectAttempts}) reached`);
          return;
        }

        // Exponential backoff with jitter
        const delay = Math.min(
          reconnectBaseDelay * Math.pow(2, currentAttempt),
          maxReconnectDelay
        );
        // Add random jitter (±20%) to prevent thundering herd
        const jitter = delay * 0.2 * (Math.random() * 2 - 1);
        const finalDelay = Math.max(0, delay + jitter);

        reconnectAttemptsRef.current = currentAttempt + 1;
        setState(prev => ({
          ...prev,
          reconnectAttempts: reconnectAttemptsRef.current,
        }));

        reconnectTimeout.current = setTimeout(connect, finalDelay);
      };

      ws.current.onerror = (error) => {
        const readyState = ws.current?.readyState;
        const readyStateLabel =
          readyState === WebSocket.CONNECTING ? "CONNECTING" :
          readyState === WebSocket.OPEN ? "OPEN" :
          readyState === WebSocket.CLOSING ? "CLOSING" :
          readyState === WebSocket.CLOSED ? "CLOSED" : String(readyState);
        console.error(`WebSocket error on ${url} (readyState: ${readyStateLabel})`);
        onError?.(error);
      };
    } catch (err) {
      console.error("Failed to create WebSocket connection:", err);
      setState(prev => ({
        ...prev,
        isConnecting: false,
      }));
    }
  }, [
    url,
    accessToken,
    enableReconnect,
    maxReconnectAttempts,
    reconnectBaseDelay,
    maxReconnectDelay,
    onConnect,
    onMessage,
    onDisconnect,
    onError,
    clearReconnectTimeout,
  ]);

  const disconnect = useCallback((code?: number, reason?: string) => {
    intentionalClose.current = true;
    clearReconnectTimeout();
    
    if (ws.current) {
      ws.current.close(code, reason);
      ws.current = null;
    }
  }, [clearReconnectTimeout]);

  const send = useCallback((data: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(typeof data === "string" ? data : JSON.stringify(data));
      return true;
    }
    return false;
  }, []);

  // Connect when component mounts or token changes
  useEffect(() => {
    if (isAuthenticated && accessToken) {
      connect();
    } else {
      disconnect();
    }
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect, isAuthenticated, accessToken]);

  // Reconnect when URL changes
  useEffect(() => {
    if (wasConnected.current) {
      disconnect();
      connect();
    }
  }, [url, connect, disconnect]);

  return {
    isConnected: state.isConnected,
    isConnecting: state.isConnecting,
    reconnectAttempts: state.reconnectAttempts,
    send,
    connect,
    disconnect,
  };
}

export default useWebSocket;

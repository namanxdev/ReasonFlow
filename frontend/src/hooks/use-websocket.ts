import { useEffect, useRef, useState, useCallback } from "react";

interface UseWebSocketOptions {
  url: string;
  onMessage?: (data: any) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export function useWebSocket({ url, onMessage, onConnect, onDisconnect }: UseWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeout = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    const token = localStorage.getItem("rf_access_token");
    if (!token) return;

    const wsUrl = `${url}?token=${token}`;
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      setIsConnected(true);
      reconnectAttempts.current = 0;
      onConnect?.();
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage?.(data);
    };

    ws.current.onclose = () => {
      setIsConnected(false);
      onDisconnect?.();
      
      // Exponential backoff reconnect
      const maxDelay = 30000; // 30 seconds max
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), maxDelay);
      reconnectAttempts.current++;
      
      reconnectTimeout.current = setTimeout(connect, delay);
    };

    ws.current.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
  }, [url, onMessage, onConnect, onDisconnect]);

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
    }
    ws.current?.close();
  }, []);

  const send = useCallback((data: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(data));
    }
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return { isConnected, send, connect, disconnect };
}

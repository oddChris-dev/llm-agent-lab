/**
 * WebSocket client for real-time execution updates.
 */

type MessageHandler = (data: any) => void;
type ConnectionHandler = () => void;

interface WebSocketMessage {
  type: string;
  data: any;
}

export class ExecutionSocket {
  private ws: WebSocket | null = null;
  private executionId: string;
  private handlers: Map<string, MessageHandler[]> = new Map();
  private onOpenHandlers: ConnectionHandler[] = [];
  private onCloseHandlers: ConnectionHandler[] = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(executionId: string) {
    this.executionId = executionId;
  }

  /**
   * Connect to the WebSocket server.
   */
  connect(): void {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const url = `${protocol}//${host}/ws/executions/${this.executionId}/`;

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log(`WebSocket connected for execution ${this.executionId}`);
      this.reconnectAttempts = 0;
      this.onOpenHandlers.forEach((handler) => handler());
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.dispatchMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onclose = () => {
      console.log(`WebSocket closed for execution ${this.executionId}`);
      this.onCloseHandlers.forEach((handler) => handler());
      this.attemptReconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  /**
   * Disconnect from the WebSocket server.
   */
  disconnect(): void {
    if (this.ws) {
      this.maxReconnectAttempts = 0; // Prevent reconnection
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Register a handler for a specific message type.
   */
  on(messageType: string, handler: MessageHandler): void {
    if (!this.handlers.has(messageType)) {
      this.handlers.set(messageType, []);
    }
    this.handlers.get(messageType)!.push(handler);
  }

  /**
   * Remove a handler for a specific message type.
   */
  off(messageType: string, handler: MessageHandler): void {
    const handlers = this.handlers.get(messageType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index !== -1) {
        handlers.splice(index, 1);
      }
    }
  }

  /**
   * Register handler for connection open.
   */
  onOpen(handler: ConnectionHandler): void {
    this.onOpenHandlers.push(handler);
  }

  /**
   * Register handler for connection close.
   */
  onClose(handler: ConnectionHandler): void {
    this.onCloseHandlers.push(handler);
  }

  /**
   * Send a ping message.
   */
  ping(): void {
    this.send({ type: 'ping' });
  }

  /**
   * Send a message to the server.
   */
  private send(data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  /**
   * Dispatch a message to registered handlers.
   */
  private dispatchMessage(message: WebSocketMessage): void {
    const handlers = this.handlers.get(message.type);
    if (handlers) {
      handlers.forEach((handler) => handler(message.data));
    }

    // Also dispatch to wildcard handlers
    const wildcardHandlers = this.handlers.get('*');
    if (wildcardHandlers) {
      wildcardHandlers.forEach((handler) => handler(message));
    }
  }

  /**
   * Attempt to reconnect after disconnection.
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

      console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);

      setTimeout(() => {
        this.connect();
      }, delay);
    }
  }

  /**
   * Get connection status.
   */
  get isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

/**
 * Create an execution socket.
 */
export function createExecutionSocket(executionId: string): ExecutionSocket {
  return new ExecutionSocket(executionId);
}

export default ExecutionSocket;

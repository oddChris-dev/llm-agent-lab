/**
 * React hooks for execution management.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useEffect, useCallback } from 'react';
import executionsApi, {
  Execution,
  NodeExecution,
  ExecutionLog,
} from '../api/executions';
import { ExecutionSocket, ExecutionMessage } from '../api/websocket';

const EXECUTIONS_KEY = 'executions';
const NODE_EXECUTIONS_KEY = 'node_executions';
const EXECUTION_LOGS_KEY = 'execution_logs';

/**
 * Hook to list executions, optionally filtered by workflow.
 */
export function useExecutions(workflowId?: string) {
  return useQuery({
    queryKey: [EXECUTIONS_KEY, { workflowId }],
    queryFn: () => executionsApi.listExecutions(workflowId),
  });
}

/**
 * Hook to get a single execution by ID.
 */
export function useExecution(executionId: string | null) {
  return useQuery({
    queryKey: [EXECUTIONS_KEY, executionId],
    queryFn: () => executionsApi.getExecution(executionId!),
    enabled: !!executionId,
    refetchInterval: (query) => {
      // Auto-refresh running executions
      const data = query.state.data;
      if (data && ['pending', 'running', 'paused'].includes(data.status)) {
        return 2000;
      }
      return false;
    },
  });
}

/**
 * Hook to get node executions for an execution.
 */
export function useNodeExecutions(executionId: string | null) {
  return useQuery({
    queryKey: [NODE_EXECUTIONS_KEY, executionId],
    queryFn: () => executionsApi.getNodeExecutions(executionId!),
    enabled: !!executionId,
  });
}

/**
 * Hook to get logs for an execution.
 */
export function useExecutionLogs(executionId: string | null) {
  return useQuery({
    queryKey: [EXECUTION_LOGS_KEY, executionId],
    queryFn: () => executionsApi.getExecutionLogs(executionId!),
    enabled: !!executionId,
  });
}

/**
 * Hook to start a workflow execution.
 */
export function useStartExecution() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      workflowId,
      triggerData,
    }: {
      workflowId: string;
      triggerData?: Record<string, any>;
    }) => executionsApi.startExecution(workflowId, triggerData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [EXECUTIONS_KEY] });
    },
  });
}

/**
 * Hook to pause a running execution.
 */
export function usePauseExecution() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (executionId: string) => executionsApi.pauseExecution(executionId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [EXECUTIONS_KEY, data.id] });
    },
  });
}

/**
 * Hook to resume a paused execution.
 */
export function useResumeExecution() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (executionId: string) => executionsApi.resumeExecution(executionId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [EXECUTIONS_KEY, data.id] });
    },
  });
}

/**
 * Hook to cancel an execution.
 */
export function useCancelExecution() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (executionId: string) => executionsApi.cancelExecution(executionId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [EXECUTIONS_KEY, data.id] });
    },
  });
}

/**
 * Hook to retry a failed execution.
 */
export function useRetryExecution() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (executionId: string) => executionsApi.retryExecution(executionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [EXECUTIONS_KEY] });
    },
  });
}

/**
 * Hook for real-time execution updates via WebSocket.
 */
export function useExecutionSocket(executionId: string | null) {
  const queryClient = useQueryClient();
  const [socket, setSocket] = useState<ExecutionSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<ExecutionMessage | null>(null);

  const handleMessage = useCallback(
    (message: ExecutionMessage) => {
      setLastMessage(message);

      // Update cache based on message type
      switch (message.type) {
        case 'execution.started':
        case 'execution.completed':
        case 'execution.failed':
        case 'execution.paused':
        case 'execution.cancelled':
          queryClient.invalidateQueries({
            queryKey: [EXECUTIONS_KEY, message.execution_id],
          });
          break;

        case 'node.started':
        case 'node.completed':
        case 'node.failed':
          queryClient.invalidateQueries({
            queryKey: [NODE_EXECUTIONS_KEY, message.execution_id],
          });
          break;

        case 'log':
          queryClient.invalidateQueries({
            queryKey: [EXECUTION_LOGS_KEY, message.execution_id],
          });
          break;
      }
    },
    [queryClient]
  );

  useEffect(() => {
    if (!executionId) {
      if (socket) {
        socket.disconnect();
        setSocket(null);
        setIsConnected(false);
      }
      return;
    }

    const ws = new ExecutionSocket(executionId);

    ws.on('open', () => setIsConnected(true));
    ws.on('close', () => setIsConnected(false));
    ws.on('error', () => setIsConnected(false));

    // Listen to all message types
    const messageTypes = [
      'execution.started',
      'execution.completed',
      'execution.failed',
      'execution.paused',
      'execution.cancelled',
      'node.started',
      'node.completed',
      'node.failed',
      'log',
      'progress',
    ];

    messageTypes.forEach((type) => {
      ws.on(type, handleMessage);
    });

    ws.connect();
    setSocket(ws);

    return () => {
      ws.disconnect();
    };
  }, [executionId, handleMessage]);

  return {
    isConnected,
    lastMessage,
    socket,
  };
}

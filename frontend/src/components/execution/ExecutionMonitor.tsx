/**
 * Execution monitoring component with real-time updates.
 */

import React from 'react';
import {
  useExecution,
  useNodeExecutions,
  useExecutionLogs,
  useExecutionSocket,
  usePauseExecution,
  useResumeExecution,
  useCancelExecution,
  useRetryExecution,
} from '../../hooks/useExecutions';

interface ExecutionMonitorProps {
  executionId: string;
  onClose?: () => void;
}

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-800',
  running: 'bg-blue-100 text-blue-800',
  paused: 'bg-yellow-100 text-yellow-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  cancelled: 'bg-gray-100 text-gray-600',
  skipped: 'bg-gray-100 text-gray-500',
};

const LOG_LEVEL_COLORS: Record<string, string> = {
  debug: 'text-gray-500',
  info: 'text-blue-600',
  warning: 'text-yellow-600',
  error: 'text-red-600',
};

export default function ExecutionMonitor({ executionId, onClose }: ExecutionMonitorProps) {
  const { data: execution, isLoading } = useExecution(executionId);
  const { data: nodeExecutions } = useNodeExecutions(executionId);
  const { data: logs } = useExecutionLogs(executionId);
  const { isConnected } = useExecutionSocket(executionId);

  const pauseMutation = usePauseExecution();
  const resumeMutation = useResumeExecution();
  const cancelMutation = useCancelExecution();
  const retryMutation = useRetryExecution();

  if (isLoading || !execution) {
    return (
      <div className="p-6 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const progress =
    execution.total_nodes > 0
      ? Math.round((execution.completed_nodes / execution.total_nodes) * 100)
      : 0;

  const canPause = execution.status === 'running';
  const canResume = execution.status === 'paused';
  const canCancel = ['pending', 'running', 'paused'].includes(execution.status);
  const canRetry = execution.status === 'failed';

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <h3 className="text-lg font-semibold text-gray-900">Execution Monitor</h3>
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
              STATUS_COLORS[execution.status]
            }`}
          >
            {execution.status}
          </span>
          {isConnected && (
            <span className="flex items-center text-xs text-green-600">
              <span className="h-2 w-2 bg-green-500 rounded-full mr-1 animate-pulse"></span>
              Live
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          {canPause && (
            <button
              onClick={() => pauseMutation.mutate(executionId)}
              disabled={pauseMutation.isPending}
              className="px-3 py-1 text-sm bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200 disabled:opacity-50"
            >
              Pause
            </button>
          )}
          {canResume && (
            <button
              onClick={() => resumeMutation.mutate(executionId)}
              disabled={resumeMutation.isPending}
              className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200 disabled:opacity-50"
            >
              Resume
            </button>
          )}
          {canCancel && (
            <button
              onClick={() => cancelMutation.mutate(executionId)}
              disabled={cancelMutation.isPending}
              className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 disabled:opacity-50"
            >
              Cancel
            </button>
          )}
          {canRetry && (
            <button
              onClick={() => retryMutation.mutate(executionId)}
              disabled={retryMutation.isPending}
              className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50"
            >
              Retry
            </button>
          )}
          {onClose && (
            <button
              onClick={onClose}
              className="p-1 text-gray-400 hover:text-gray-600"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Progress */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-600">Progress</span>
          <span className="text-sm font-medium text-gray-900">
            {execution.completed_nodes}/{execution.total_nodes} nodes ({progress}%)
          </span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${
              execution.status === 'failed' ? 'bg-red-500' : 'bg-blue-500'
            }`}
            style={{ width: `${progress}%` }}
          ></div>
        </div>
        {execution.failed_nodes > 0 && (
          <p className="mt-1 text-xs text-red-600">
            {execution.failed_nodes} node(s) failed
          </p>
        )}
      </div>

      {/* Node Executions */}
      <div className="px-6 py-4 border-b border-gray-200">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Node Executions</h4>
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {nodeExecutions?.map((node) => (
            <div
              key={node.id}
              className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded"
            >
              <span className="text-sm text-gray-700">{node.node_id}</span>
              <span
                className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                  STATUS_COLORS[node.status]
                }`}
              >
                {node.status}
              </span>
            </div>
          ))}
          {(!nodeExecutions || nodeExecutions.length === 0) && (
            <p className="text-sm text-gray-500">No node executions yet</p>
          )}
        </div>
      </div>

      {/* Logs */}
      <div className="px-6 py-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Logs</h4>
        <div className="space-y-1 max-h-64 overflow-y-auto font-mono text-xs bg-gray-900 rounded p-3">
          {logs?.map((log) => (
            <div key={log.id} className="flex">
              <span className="text-gray-500 mr-2">
                {new Date(log.timestamp).toLocaleTimeString()}
              </span>
              <span className={`mr-2 ${LOG_LEVEL_COLORS[log.level]}`}>
                [{log.level.toUpperCase()}]
              </span>
              <span className="text-gray-300">{log.message}</span>
            </div>
          ))}
          {(!logs || logs.length === 0) && (
            <p className="text-gray-500">No logs yet</p>
          )}
        </div>
      </div>

      {/* Timestamps */}
      <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 text-xs text-gray-500">
        <div className="flex justify-between">
          <span>
            Started: {execution.started_at ? new Date(execution.started_at).toLocaleString() : 'Not started'}
          </span>
          <span>
            Completed: {execution.completed_at ? new Date(execution.completed_at).toLocaleString() : 'In progress'}
          </span>
        </div>
      </div>
    </div>
  );
}

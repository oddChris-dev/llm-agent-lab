/**
 * Execution API service.
 */

import apiClient from './client';

export interface Execution {
  id: string;
  workflow_id: string;
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  trigger_type: string;
  trigger_data: Record<string, any>;
  context: Record<string, any>;
  started_at: string | null;
  completed_at: string | null;
  total_nodes: number;
  completed_nodes: number;
  failed_nodes: number;
  created_at: string;
  updated_at: string;
}

export interface NodeExecution {
  id: string;
  execution_id: string;
  node_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  output: any;
  error: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface ExecutionLog {
  id: string;
  execution_id: string;
  level: 'debug' | 'info' | 'warning' | 'error';
  message: string;
  node_id: string | null;
  data: Record<string, any>;
  timestamp: string;
}

/**
 * Start a workflow execution.
 */
export async function startExecution(
  workflowId: string,
  triggerData?: Record<string, any>
): Promise<Execution> {
  const response = await apiClient.post<{ data: Execution }>(
    `/workflows/${workflowId}/execute/`,
    { trigger_data: triggerData }
  );
  return response.data.data;
}

/**
 * List executions for a workflow.
 */
export async function listExecutions(workflowId?: string): Promise<Execution[]> {
  const url = workflowId ? `/executions/?workflow=${workflowId}` : '/executions/';
  const response = await apiClient.get<{ data: Execution[] }>(url);
  return response.data.data;
}

/**
 * Get an execution by ID.
 */
export async function getExecution(executionId: string): Promise<Execution> {
  const response = await apiClient.get<{ data: Execution }>(`/executions/${executionId}/`);
  return response.data.data;
}

/**
 * Pause a running execution.
 */
export async function pauseExecution(executionId: string): Promise<Execution> {
  const response = await apiClient.post<{ data: Execution }>(
    `/executions/${executionId}/pause/`
  );
  return response.data.data;
}

/**
 * Resume a paused execution.
 */
export async function resumeExecution(executionId: string): Promise<Execution> {
  const response = await apiClient.post<{ data: Execution }>(
    `/executions/${executionId}/resume/`
  );
  return response.data.data;
}

/**
 * Cancel an execution.
 */
export async function cancelExecution(executionId: string): Promise<Execution> {
  const response = await apiClient.post<{ data: Execution }>(
    `/executions/${executionId}/cancel/`
  );
  return response.data.data;
}

/**
 * Retry a failed execution.
 */
export async function retryExecution(executionId: string): Promise<Execution> {
  const response = await apiClient.post<{ data: Execution }>(
    `/executions/${executionId}/retry/`
  );
  return response.data.data;
}

/**
 * Get node executions for an execution.
 */
export async function getNodeExecutions(executionId: string): Promise<NodeExecution[]> {
  const response = await apiClient.get<{ data: NodeExecution[] }>(
    `/executions/${executionId}/nodes/`
  );
  return response.data.data;
}

/**
 * Get logs for an execution.
 */
export async function getExecutionLogs(executionId: string): Promise<ExecutionLog[]> {
  const response = await apiClient.get<{ data: ExecutionLog[] }>(
    `/executions/${executionId}/logs/`
  );
  return response.data.data;
}

/**
 * Get execution progress.
 */
export async function getExecutionProgress(
  executionId: string
): Promise<{
  total_nodes: number;
  completed_nodes: number;
  failed_nodes: number;
  running_nodes: number;
  percent_complete: number;
}> {
  const response = await apiClient.get(`/executions/${executionId}/progress/`);
  return response.data;
}

export default {
  startExecution,
  listExecutions,
  getExecution,
  pauseExecution,
  resumeExecution,
  cancelExecution,
  retryExecution,
  getNodeExecutions,
  getExecutionLogs,
  getExecutionProgress,
};

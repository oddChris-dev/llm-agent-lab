/**
 * Executions history page with filtering and detail view.
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Play,
  Clock,
  CheckCircle,
  XCircle,
  Pause,
  AlertTriangle,
  Search,
  Filter,
  ChevronRight,
  Loader2,
  RotateCcw,
} from 'lucide-react';
import { useExecutions } from '../../hooks/useExecutions';
import { useWorkflows } from '../../hooks/useWorkflows';
import type { Execution } from '../../api/executions';
import ExecutionDetailModal from './ExecutionDetailModal';

const STATUS_CONFIG: Record<string, { icon: React.ReactNode; color: string; bgColor: string }> = {
  pending: {
    icon: <Clock className="w-4 h-4" />,
    color: 'text-gray-600',
    bgColor: 'bg-gray-100 dark:bg-gray-700',
  },
  running: {
    icon: <Play className="w-4 h-4" />,
    color: 'text-blue-600',
    bgColor: 'bg-blue-100 dark:bg-blue-900/30',
  },
  paused: {
    icon: <Pause className="w-4 h-4" />,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-100 dark:bg-yellow-900/30',
  },
  completed: {
    icon: <CheckCircle className="w-4 h-4" />,
    color: 'text-green-600',
    bgColor: 'bg-green-100 dark:bg-green-900/30',
  },
  failed: {
    icon: <XCircle className="w-4 h-4" />,
    color: 'text-red-600',
    bgColor: 'bg-red-100 dark:bg-red-900/30',
  },
  cancelled: {
    icon: <AlertTriangle className="w-4 h-4" />,
    color: 'text-gray-500',
    bgColor: 'bg-gray-100 dark:bg-gray-700',
  },
};

function formatDuration(startedAt: string | null, completedAt: string | null): string {
  if (!startedAt) return '-';
  const start = new Date(startedAt).getTime();
  const end = completedAt ? new Date(completedAt).getTime() : Date.now();
  const duration = end - start;

  if (duration < 1000) return `${duration}ms`;
  if (duration < 60000) return `${(duration / 1000).toFixed(1)}s`;
  return `${Math.floor(duration / 60000)}m ${Math.floor((duration % 60000) / 1000)}s`;
}

function formatDate(date: string): string {
  return new Date(date).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function ExecutionsPage() {
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [workflowFilter, setWorkflowFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedExecution, setSelectedExecution] = useState<Execution | null>(null);

  const { data: executions, isLoading, error, refetch } = useExecutions();
  const { data: workflows } = useWorkflows();

  // Filter executions
  const filteredExecutions = executions?.filter((execution) => {
    if (statusFilter && execution.status !== statusFilter) return false;
    if (workflowFilter && execution.workflow_id !== workflowFilter) return false;
    return true;
  });

  // Get workflow name for an execution
  const getWorkflowName = (workflowId: string) => {
    const workflow = workflows?.find((w) => w.id === workflowId);
    return workflow?.name || 'Unknown Workflow';
  };

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-500">Failed to load executions. Please try again.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Executions
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            View execution history and results
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center gap-2 px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Status filter */}
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setStatusFilter('')}
            className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
              statusFilter === ''
                ? 'bg-primary-500 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            All
          </button>
          {['running', 'completed', 'failed', 'paused', 'cancelled'].map((status) => {
            const config = STATUS_CONFIG[status];
            return (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg transition-colors ${
                  statusFilter === status
                    ? 'bg-primary-500 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                {config.icon}
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </button>
            );
          })}
        </div>

        {/* Workflow filter */}
        <select
          value={workflowFilter}
          onChange={(e) => setWorkflowFilter(e.target.value)}
          className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        >
          <option value="">All Workflows</option>
          {workflows?.map((workflow) => (
            <option key={workflow.id} value={workflow.id}>
              {workflow.name}
            </option>
          ))}
        </select>
      </div>

      {/* Executions List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
        </div>
      ) : filteredExecutions?.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 dark:bg-gray-800/50 rounded-lg border-2 border-dashed border-gray-200 dark:border-gray-700">
          <Clock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400">
            {statusFilter || workflowFilter
              ? 'No executions match your filters'
              : 'No executions yet. Run a workflow to see results here.'}
          </p>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700/50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Workflow
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Progress
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Duration
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Started
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {filteredExecutions?.map((execution) => {
                const statusConfig = STATUS_CONFIG[execution.status];
                const progress =
                  execution.total_nodes > 0
                    ? Math.round((execution.completed_nodes / execution.total_nodes) * 100)
                    : 0;

                return (
                  <tr
                    key={execution.id}
                    className="hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer"
                    onClick={() => setSelectedExecution(execution)}
                  >
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${statusConfig.bgColor} ${statusConfig.color}`}
                      >
                        {statusConfig.icon}
                        {execution.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        to={`/workflows/${execution.workflow_id}`}
                        onClick={(e) => e.stopPropagation()}
                        className="text-sm font-medium text-gray-900 dark:text-white hover:text-primary-500"
                      >
                        {getWorkflowName(execution.workflow_id)}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                          <div
                            className={`h-full transition-all ${
                              execution.status === 'failed' ? 'bg-red-500' : 'bg-green-500'
                            }`}
                            style={{ width: `${progress}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500">
                          {execution.completed_nodes}/{execution.total_nodes}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">
                      {formatDuration(execution.started_at, execution.completed_at)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                      {execution.started_at ? formatDate(execution.started_at) : '-'}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedExecution(execution);
                        }}
                        className="text-gray-400 hover:text-primary-500"
                      >
                        <ChevronRight className="w-5 h-5" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Execution Detail Modal */}
      {selectedExecution && (
        <ExecutionDetailModal
          executionId={selectedExecution.id}
          onClose={() => setSelectedExecution(null)}
        />
      )}
    </div>
  );
}

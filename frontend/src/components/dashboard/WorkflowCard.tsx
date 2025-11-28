import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Play, Pause, Settings, MoreVertical, Clock, Loader2 } from 'lucide-react';
import type { Workflow } from '../../types/workflow';
import { useUpdateWorkflow, useDeleteWorkflow, useDuplicateWorkflow, useExecuteWorkflow } from '../../hooks/useWorkflows';

interface WorkflowCardProps {
  workflow: Workflow;
}

const statusColors = {
  draft: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  active: 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-400',
  archived: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/50 dark:text-yellow-400',
};

const statusIcons = {
  draft: null,
  active: <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />,
  archived: null,
};

export default function WorkflowCard({ workflow }: WorkflowCardProps) {
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = React.useState(false);
  const updateWorkflow = useUpdateWorkflow();
  const deleteWorkflow = useDeleteWorkflow();
  const duplicateWorkflow = useDuplicateWorkflow();
  const executeWorkflow = useExecuteWorkflow();

  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleToggleStatus = () => {
    const newStatus = workflow.status === 'active' ? 'draft' : 'active';
    updateWorkflow.mutate({
      id: workflow.id,
      data: { status: newStatus },
    });
  };

  const handleDuplicate = () => {
    setMenuOpen(false);
    duplicateWorkflow.mutate({ id: workflow.id });
  };

  const handleDelete = () => {
    if (window.confirm(`Are you sure you want to delete "${workflow.name}"?`)) {
      setMenuOpen(false);
      deleteWorkflow.mutate(workflow.id);
    }
  };

  const handleRun = () => {
    executeWorkflow.mutate(
      { id: workflow.id },
      {
        onSuccess: (response) => {
          navigate(`/workflows/${workflow.id}?execution=${response.data.id}`);
        },
      }
    );
  };

  const isUpdating = updateWorkflow.isPending;
  const isRunning = executeWorkflow.isPending;

  return (
    <div className="relative bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <Link to={`/workflows/${workflow.id}`} className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{workflow.icon || '🤖'}</span>
            <h3 className="font-semibold text-gray-900 dark:text-white truncate">
              {workflow.name}
            </h3>
          </div>
        </Link>

        <div className="relative">
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded"
          >
            <MoreVertical className="w-5 h-5" />
          </button>

          {menuOpen && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setMenuOpen(false)}
              />
              <div className="absolute right-0 mt-1 w-48 bg-white dark:bg-gray-700 rounded-lg shadow-lg border border-gray-200 dark:border-gray-600 py-1 z-20">
                <Link
                  to={`/workflows/${workflow.id}`}
                  className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600"
                >
                  Edit
                </Link>
                <button
                  onClick={handleToggleStatus}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600"
                >
                  {workflow.status === 'active' ? 'Set to Draft' : 'Activate'}
                </button>
                <button
                  onClick={handleDuplicate}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600"
                >
                  Duplicate
                </button>
                <button
                  onClick={handleDelete}
                  className="w-full text-left px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-600"
                >
                  Delete
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Description */}
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-4 line-clamp-2">
        {workflow.description || 'No description'}
      </p>

      {/* Status badge */}
      <div className="flex items-center gap-2 mb-4">
        <button
          onClick={handleToggleStatus}
          disabled={isUpdating}
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium cursor-pointer hover:opacity-80 transition-opacity ${
            statusColors[workflow.status]
          } ${isUpdating ? 'opacity-50' : ''}`}
          title={`Click to ${workflow.status === 'active' ? 'deactivate' : 'activate'}`}
        >
          {isUpdating ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : (
            statusIcons[workflow.status]
          )}
          {workflow.status.charAt(0).toUpperCase() + workflow.status.slice(1)}
        </button>
        <span className="text-xs text-gray-400">
          {workflow.node_count} nodes
        </span>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100 dark:border-gray-700">
        <div className="flex items-center gap-1 text-xs text-gray-400">
          <Clock className="w-3.5 h-3.5" />
          <span>Updated {formatDate(workflow.updated_at)}</span>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={handleRun}
            disabled={isRunning}
            className="p-1.5 text-gray-400 hover:text-green-500 rounded transition-colors disabled:opacity-50"
            title="Run workflow"
          >
            {isRunning ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
          </button>
          <Link
            to={`/workflows/${workflow.id}`}
            className="p-1.5 text-gray-400 hover:text-primary-500 rounded transition-colors"
            title="Edit"
          >
            <Settings className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}

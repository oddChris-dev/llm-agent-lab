import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Play, Pause, Settings, MoreVertical } from 'lucide-react';
import { useWorkflows } from '../../hooks/useWorkflows';
import WorkflowCard from './WorkflowCard';
import QuickStats from './QuickStats';
import CreateWorkflowModal from '../workflows/CreateWorkflowModal';

export default function Dashboard() {
  const { data: workflows, isLoading, error } = useWorkflows();
  const [showCreateModal, setShowCreateModal] = useState(false);

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-500">Failed to load workflows. Please try again.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Dashboard
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Manage your AI agent workflows
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
        >
          <Plus className="w-5 h-5" />
          New Workflow
        </button>
      </div>

      {/* Quick Stats */}
      <QuickStats />

      {/* Workflows Grid */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          My Workflows
        </h2>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-48 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"
              />
            ))}
          </div>
        ) : workflows?.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 dark:bg-gray-800/50 rounded-lg border-2 border-dashed border-gray-200 dark:border-gray-700">
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              No workflows yet. Create your first one!
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
            >
              <Plus className="w-5 h-5" />
              Create Workflow
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {workflows?.map((workflow) => (
              <WorkflowCard key={workflow.id} workflow={workflow} />
            ))}

            {/* Add new card */}
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex flex-col items-center justify-center h-48 bg-gray-50 dark:bg-gray-800/50 rounded-lg border-2 border-dashed border-gray-200 dark:border-gray-700 hover:border-primary-500 dark:hover:border-primary-500 transition-colors group"
            >
              <Plus className="w-8 h-8 text-gray-400 group-hover:text-primary-500 transition-colors" />
              <span className="mt-2 text-gray-500 group-hover:text-primary-500 transition-colors">
                New Workflow
              </span>
            </button>
          </div>
        )}
      </div>

      {/* Create Workflow Modal */}
      {showCreateModal && (
        <CreateWorkflowModal onClose={() => setShowCreateModal(false)} />
      )}
    </div>
  );
}

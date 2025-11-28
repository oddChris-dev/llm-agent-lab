import React from 'react';
import { GitBranch, Play, ListTodo, CheckCircle } from 'lucide-react';
import { useDashboardStats } from '../../hooks/useDashboard';

export default function QuickStats() {
  const { data: dashboardStats, isLoading } = useDashboardStats();

  const stats = [
    {
      label: 'Total Workflows',
      value: dashboardStats?.total_workflows ?? 0,
      icon: GitBranch,
      color: 'text-primary-500',
      bgColor: 'bg-primary-50 dark:bg-primary-900/30',
    },
    {
      label: 'Running',
      value: dashboardStats?.running_executions ?? 0,
      icon: Play,
      color: 'text-green-500',
      bgColor: 'bg-green-50 dark:bg-green-900/30',
    },
    {
      label: 'Queued Tasks',
      value: dashboardStats?.queued_tasks ?? 0,
      icon: ListTodo,
      color: 'text-yellow-500',
      bgColor: 'bg-yellow-50 dark:bg-yellow-900/30',
    },
    {
      label: 'Completed Today',
      value: dashboardStats?.completed_today ?? 0,
      icon: CheckCircle,
      color: 'text-cyan-500',
      bgColor: 'bg-cyan-50 dark:bg-cyan-900/30',
    },
  ];

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 animate-pulse"
          >
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-gray-200 dark:bg-gray-700 rounded-lg" />
              <div>
                <div className="h-6 w-12 bg-gray-200 dark:bg-gray-700 rounded mb-1" />
                <div className="h-4 w-20 bg-gray-200 dark:bg-gray-700 rounded" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4"
        >
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${stat.bgColor}`}>
              <stat.icon className={`w-5 h-5 ${stat.color}`} />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {stat.value.toLocaleString()}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {stat.label}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

import React from 'react';
import { GitBranch, Play, ListTodo, CheckCircle } from 'lucide-react';

export default function QuickStats() {
  // These would come from an API call
  const stats = [
    {
      label: 'Total Workflows',
      value: 12,
      icon: GitBranch,
      color: 'text-primary-500',
      bgColor: 'bg-primary-50 dark:bg-primary-900/30',
    },
    {
      label: 'Running',
      value: 3,
      icon: Play,
      color: 'text-green-500',
      bgColor: 'bg-green-50 dark:bg-green-900/30',
    },
    {
      label: 'Queued Tasks',
      value: 47,
      icon: ListTodo,
      color: 'text-yellow-500',
      bgColor: 'bg-yellow-50 dark:bg-yellow-900/30',
    },
    {
      label: 'Completed Today',
      value: 1234,
      icon: CheckCircle,
      color: 'text-cyan-500',
      bgColor: 'bg-cyan-50 dark:bg-cyan-900/30',
    },
  ];

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

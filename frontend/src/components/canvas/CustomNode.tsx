import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import {
  Bot,
  Volume2,
  Globe,
  List,
  Image,
  Zap,
  GitBranch,
  Send,
} from 'lucide-react';

const categoryIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  llm: Bot,
  voice: Volume2,
  web: Globe,
  queue: List,
  image: Image,
  trigger: Zap,
  control: GitBranch,
  output: Send,
};

const categoryColors: Record<string, string> = {
  llm: 'border-l-cyan-500',
  voice: 'border-l-pink-500',
  web: 'border-l-teal-500',
  queue: 'border-l-yellow-500',
  image: 'border-l-orange-500',
  trigger: 'border-l-purple-500',
  control: 'border-l-indigo-500',
  output: 'border-l-green-500',
};

interface CustomNodeData {
  label: string;
  type: string;
  config?: Record<string, unknown>;
}

function CustomNode({ data, selected }: NodeProps<CustomNodeData>) {
  const category = data.type.split('.')[0];
  const Icon = categoryIcons[category] || Bot;
  const borderColor = categoryColors[category] || 'border-l-gray-500';

  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 border-l-4 ${borderColor} min-w-[160px] ${
        selected ? 'ring-2 ring-primary-500' : ''
      }`}
    >
      {/* Input handles */}
      <Handle
        type="target"
        position={Position.Left}
        className="!w-3 !h-3 !bg-gray-400 !border-2 !border-white dark:!border-gray-800"
      />

      {/* Node content */}
      <div className="p-3">
        <div className="flex items-center gap-2 mb-1">
          <Icon className="w-4 h-4 text-gray-500 dark:text-gray-400" />
          <span className="font-medium text-sm text-gray-900 dark:text-white truncate">
            {data.label}
          </span>
        </div>
        <span className="text-xs text-gray-400 dark:text-gray-500">
          {data.type}
        </span>
      </div>

      {/* Output handles */}
      <Handle
        type="source"
        position={Position.Right}
        className="!w-3 !h-3 !bg-gray-400 !border-2 !border-white dark:!border-gray-800"
      />
    </div>
  );
}

export default memo(CustomNode);

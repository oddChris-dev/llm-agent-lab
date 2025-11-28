import React, { useState } from 'react';
import { Node } from 'reactflow';
import { X, Save } from 'lucide-react';

interface NodeConfigPanelProps {
  node: Node;
  onClose: () => void;
  onUpdate: (data: Node['data']) => void;
}

export default function NodeConfigPanel({
  node,
  onClose,
  onUpdate,
}: NodeConfigPanelProps) {
  const [label, setLabel] = useState(node.data.label);
  const [config, setConfig] = useState(JSON.stringify(node.data.config || {}, null, 2));
  const [configError, setConfigError] = useState<string | null>(null);

  const handleSave = () => {
    try {
      const parsedConfig = JSON.parse(config);
      setConfigError(null);
      onUpdate({
        ...node.data,
        label,
        config: parsedConfig,
      });
    } catch (e) {
      setConfigError('Invalid JSON configuration');
    }
  };

  const nodeType = node.data.type;
  const category = nodeType.split('.')[0];

  return (
    <div className="absolute top-0 right-0 w-80 h-full bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 shadow-lg flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        <div>
          <h2 className="font-semibold text-gray-900 dark:text-white">
            Configure Node
          </h2>
          <p className="text-xs text-gray-500 dark:text-gray-400">{nodeType}</p>
        </div>
        <button
          onClick={onClose}
          className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Name
          </label>
          <input
            type="text"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        {/* Type-specific config fields */}
        {category === 'llm' && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                System Prompt
              </label>
              <textarea
                rows={4}
                placeholder="You are a helpful assistant..."
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Temperature
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                defaultValue="0.7"
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>Precise</span>
                <span>Creative</span>
              </div>
            </div>
          </>
        )}

        {category === 'voice' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Voice
            </label>
            <select className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500">
              <option value="">Select voice...</option>
              <option value="default">Default</option>
              <option value="custom">Custom Voice</option>
            </select>
          </div>
        )}

        {category === 'queue' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Max Size
            </label>
            <input
              type="number"
              defaultValue={1000}
              className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        )}

        {/* Raw config JSON */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Configuration (JSON)
          </label>
          <textarea
            rows={8}
            value={config}
            onChange={(e) => {
              setConfig(e.target.value);
              setConfigError(null);
            }}
            className={`w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none ${
              configError
                ? 'border-red-500'
                : 'border-gray-200 dark:border-gray-600'
            }`}
          />
          {configError && (
            <p className="text-xs text-red-500 mt-1">{configError}</p>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <button
          onClick={handleSave}
          className="w-full inline-flex items-center justify-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
        >
          <Save className="w-4 h-4" />
          Save Changes
        </button>
      </div>
    </div>
  );
}

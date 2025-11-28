import React, { useState } from 'react';
import { X, Search } from 'lucide-react';

interface NodeType {
  type: string;
  name: string;
  description: string;
  category: string;
}

const NODE_TYPES: NodeType[] = [
  // Triggers
  { type: 'trigger.manual', name: 'Manual Trigger', description: 'Start workflow manually', category: 'trigger' },
  { type: 'trigger.schedule', name: 'Schedule', description: 'Trigger on schedule', category: 'trigger' },
  { type: 'trigger.webhook', name: 'Webhook', description: 'Trigger via HTTP', category: 'trigger' },

  // LLM
  { type: 'llm.claude', name: 'Claude', description: 'Anthropic Claude', category: 'llm' },
  { type: 'llm.openai', name: 'GPT', description: 'OpenAI GPT models', category: 'llm' },
  { type: 'llm.ollama', name: 'Ollama', description: 'Local LLM via Ollama', category: 'llm' },

  // Voice
  { type: 'voice.tts', name: 'Text to Speech', description: 'Convert text to audio', category: 'voice' },
  { type: 'voice.stt', name: 'Speech to Text', description: 'Convert audio to text', category: 'voice' },

  // Web
  { type: 'web.browser_watch', name: 'Browser Watch', description: 'Watch browser navigation', category: 'web' },
  { type: 'web.search', name: 'Web Search', description: 'Search the web', category: 'web' },
  { type: 'web.fetch', name: 'Fetch Page', description: 'Fetch and parse web page', category: 'web' },

  // Queue
  { type: 'queue.fifo', name: 'FIFO Queue', description: 'First in, first out', category: 'queue' },
  { type: 'queue.round_robin', name: 'Round Robin', description: 'Distribute across outputs', category: 'queue' },
  { type: 'queue.broadcast', name: 'Broadcast', description: 'Send to all outputs', category: 'queue' },

  // Image
  { type: 'image.generate', name: 'Generate Image', description: 'Generate from text', category: 'image' },

  // Control
  { type: 'control.condition', name: 'Condition', description: 'Conditional branching', category: 'control' },
  { type: 'control.loop', name: 'Loop', description: 'Iterate over items', category: 'control' },

  // Output
  { type: 'output.display', name: 'Display', description: 'Show output to user', category: 'output' },
];

const CATEGORIES = [
  { id: 'all', name: 'All' },
  { id: 'trigger', name: 'Triggers' },
  { id: 'llm', name: 'LLM' },
  { id: 'voice', name: 'Voice' },
  { id: 'web', name: 'Web' },
  { id: 'queue', name: 'Queue' },
  { id: 'image', name: 'Image' },
  { id: 'control', name: 'Control' },
  { id: 'output', name: 'Output' },
];

const categoryColors: Record<string, string> = {
  trigger: 'bg-purple-100 text-purple-700 dark:bg-purple-900/50 dark:text-purple-300',
  llm: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/50 dark:text-cyan-300',
  voice: 'bg-pink-100 text-pink-700 dark:bg-pink-900/50 dark:text-pink-300',
  web: 'bg-teal-100 text-teal-700 dark:bg-teal-900/50 dark:text-teal-300',
  queue: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/50 dark:text-yellow-300',
  image: 'bg-orange-100 text-orange-700 dark:bg-orange-900/50 dark:text-orange-300',
  control: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300',
  output: 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300',
};

interface NodeLibraryProps {
  onSelect: (type: string) => void;
  onClose: () => void;
}

export default function NodeLibrary({ onSelect, onClose }: NodeLibraryProps) {
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  const filteredNodes = NODE_TYPES.filter((node) => {
    const matchesSearch =
      search === '' ||
      node.name.toLowerCase().includes(search.toLowerCase()) ||
      node.description.toLowerCase().includes(search.toLowerCase());

    const matchesCategory =
      selectedCategory === 'all' || node.category === selectedCategory;

    return matchesSearch && matchesCategory;
  });

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-y-4 right-4 w-96 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 z-50 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="font-semibold text-gray-900 dark:text-white">
            Add Node
          </h2>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search nodes..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>

        {/* Categories */}
        <div className="flex gap-2 p-4 overflow-x-auto border-b border-gray-200 dark:border-gray-700">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-3 py-1 text-xs font-medium rounded-full whitespace-nowrap transition-colors ${
                selectedCategory === cat.id
                  ? 'bg-primary-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              {cat.name}
            </button>
          ))}
        </div>

        {/* Node list */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {filteredNodes.map((node) => (
            <button
              key={node.type}
              onClick={() => onSelect(node.type)}
              className="w-full text-left p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-gray-900 dark:text-white">
                  {node.name}
                </span>
                <span
                  className={`px-2 py-0.5 text-xs rounded-full ${
                    categoryColors[node.category]
                  }`}
                >
                  {node.category}
                </span>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {node.description}
              </p>
            </button>
          ))}

          {filteredNodes.length === 0 && (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              No nodes found
            </div>
          )}
        </div>
      </div>
    </>
  );
}

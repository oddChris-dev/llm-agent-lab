import React, { useState, useEffect } from 'react';
import { Node } from 'reactflow';
import { X, Save, Loader2 } from 'lucide-react';
import { useProviders, useProviderVoices } from '../../hooks/useProviders';

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

  // For voice nodes: provider and voice selection
  const [selectedProviderId, setSelectedProviderId] = useState<string>(
    node.data.config?.provider_id || ''
  );
  const [selectedVoiceId, setSelectedVoiceId] = useState<string>(
    node.data.config?.voice_id || ''
  );

  // Fetch TTS providers
  const { data: providers } = useProviders('tts');
  const ttsProviders = providers || [];

  // Fetch voices for selected provider
  const { data: voices, isLoading: voicesLoading } = useProviderVoices(
    selectedProviderId || null
  );

  // Update config when provider or voice changes
  useEffect(() => {
    if (node.data.type?.startsWith('voice.')) {
      const currentConfig = JSON.parse(config);
      const newConfig = {
        ...currentConfig,
        provider_id: selectedProviderId || undefined,
        voice_id: selectedVoiceId || undefined,
      };
      setConfig(JSON.stringify(newConfig, null, 2));
    }
  }, [selectedProviderId, selectedVoiceId]);

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
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                TTS Provider
              </label>
              <select
                value={selectedProviderId}
                onChange={(e) => {
                  setSelectedProviderId(e.target.value);
                  setSelectedVoiceId(''); // Reset voice when provider changes
                }}
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">Select provider...</option>
                {ttsProviders.map((provider) => (
                  <option key={provider.id} value={provider.id}>
                    {provider.name}
                  </option>
                ))}
              </select>
              {ttsProviders.length === 0 && (
                <p className="text-xs text-amber-500 mt-1">
                  No TTS providers configured. Add one in Settings.
                </p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Voice
              </label>
              <div className="relative">
                <select
                  value={selectedVoiceId}
                  onChange={(e) => setSelectedVoiceId(e.target.value)}
                  disabled={!selectedProviderId || voicesLoading}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
                >
                  <option value="">Select voice...</option>
                  {voices?.map((voice) => (
                    <option key={voice.id} value={voice.id}>
                      {voice.name} {voice.is_cloned && '(cloned)'}
                    </option>
                  ))}
                </select>
                {voicesLoading && (
                  <Loader2 className="absolute right-8 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin text-gray-400" />
                )}
              </div>
              {selectedProviderId && voices?.length === 0 && !voicesLoading && (
                <p className="text-xs text-amber-500 mt-1">
                  No voices available. Upload a voice sample in Assets.
                </p>
              )}
            </div>
          </>
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

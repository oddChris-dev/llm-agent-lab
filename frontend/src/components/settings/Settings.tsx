import React, { useState, useEffect } from 'react';
import { Key, Database, Volume2, Image, CheckCircle, XCircle, Loader2, Plus, Trash2 } from 'lucide-react';
import {
  useProviders,
  useCreateProvider,
  useUpdateProvider,
  useDeleteProvider,
  useTestProvider,
} from '../../hooks/useProviders';
import type { Provider, CreateProviderData } from '../../api/providers';

interface ProviderFormData {
  anthropic_api_key: string;
  openai_api_key: string;
  ollama_url: string;
  tts_provider: string;
  tts_url: string;
  stt_provider: string;
  comfyui_url: string;
}

interface TestStatus {
  [key: string]: {
    testing: boolean;
    success?: boolean;
    message?: string;
    latency?: number;
  };
}

export default function Settings() {
  const { data: providers, isLoading } = useProviders();
  const createProvider = useCreateProvider();
  const updateProvider = useUpdateProvider();
  const deleteProvider = useDeleteProvider();
  const testProvider = useTestProvider();

  const [formData, setFormData] = useState<ProviderFormData>({
    anthropic_api_key: '',
    openai_api_key: '',
    ollama_url: 'http://localhost:11434',
    tts_provider: 'xtts',
    tts_url: 'http://localhost:8020',
    stt_provider: 'vosk',
    comfyui_url: 'http://localhost:8188',
  });

  const [testStatus, setTestStatus] = useState<TestStatus>({});
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Load existing provider configs
  useEffect(() => {
    if (providers) {
      const newFormData = { ...formData };

      providers.forEach((provider: Provider) => {
        if (provider.type === 'llm') {
          const llmType = provider.config?.type;
          if (llmType === 'anthropic') {
            newFormData.anthropic_api_key = provider.config?.api_key || '';
          } else if (llmType === 'openai') {
            newFormData.openai_api_key = provider.config?.api_key || '';
          } else if (llmType === 'ollama') {
            newFormData.ollama_url = provider.config?.base_url || 'http://localhost:11434';
          }
        } else if (provider.type === 'tts') {
          newFormData.tts_provider = provider.config?.type || 'xtts';
          newFormData.tts_url = provider.config?.base_url || '';
        } else if (provider.type === 'stt') {
          newFormData.stt_provider = provider.config?.type || 'vosk';
        } else if (provider.type === 'image') {
          newFormData.comfyui_url = provider.config?.base_url || 'http://localhost:8188';
        }
      });

      setFormData(newFormData);
    }
  }, [providers]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setSaveMessage(null);
  };

  const handleTest = async (providerType: string) => {
    const provider = providers?.find((p: Provider) => {
      if (providerType === 'ollama') return p.type === 'llm' && p.config?.type === 'ollama';
      if (providerType === 'anthropic') return p.type === 'llm' && p.config?.type === 'anthropic';
      if (providerType === 'openai') return p.type === 'llm' && p.config?.type === 'openai';
      if (providerType === 'tts') return p.type === 'tts';
      if (providerType === 'image') return p.type === 'image';
      return false;
    });

    if (!provider) {
      setTestStatus((prev) => ({
        ...prev,
        [providerType]: { testing: false, success: false, message: 'Provider not configured' },
      }));
      return;
    }

    setTestStatus((prev) => ({
      ...prev,
      [providerType]: { testing: true },
    }));

    try {
      const result = await testProvider.mutateAsync(provider.id);
      setTestStatus((prev) => ({
        ...prev,
        [providerType]: {
          testing: false,
          success: result.success,
          message: result.message,
          latency: result.latency_ms,
        },
      }));
    } catch (error) {
      setTestStatus((prev) => ({
        ...prev,
        [providerType]: {
          testing: false,
          success: false,
          message: error instanceof Error ? error.message : 'Test failed',
        },
      }));
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setSaveMessage(null);

    try {
      // Create or update providers based on form data
      const providerConfigs = [
        {
          name: 'Ollama',
          slug: 'ollama',
          type: 'llm' as const,
          config: { type: 'ollama', base_url: formData.ollama_url },
        },
        {
          name: 'Anthropic',
          slug: 'anthropic',
          type: 'llm' as const,
          config: { type: 'anthropic', api_key: formData.anthropic_api_key },
        },
        {
          name: 'OpenAI',
          slug: 'openai',
          type: 'llm' as const,
          config: { type: 'openai', api_key: formData.openai_api_key },
        },
        {
          name: 'TTS',
          slug: 'tts',
          type: 'tts' as const,
          config: { type: formData.tts_provider, base_url: formData.tts_url },
        },
        {
          name: 'STT',
          slug: 'stt',
          type: 'stt' as const,
          config: { type: formData.stt_provider },
        },
        {
          name: 'ComfyUI',
          slug: 'comfyui',
          type: 'image' as const,
          config: { type: 'comfyui', base_url: formData.comfyui_url },
        },
      ];

      for (const config of providerConfigs) {
        // Skip if no meaningful config
        if (config.type === 'llm' && config.config.type !== 'ollama' && !config.config.api_key) {
          continue;
        }

        const existing = providers?.find(
          (p: Provider) => p.slug === config.slug || (p.type === config.type && p.config?.type === config.config.type)
        );

        if (existing) {
          await updateProvider.mutateAsync({
            id: existing.id,
            data: { config: config.config },
          });
        } else {
          await createProvider.mutateAsync(config);
        }
      }

      setSaveMessage({ type: 'success', text: 'Settings saved successfully' });
    } catch (error) {
      setSaveMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'Failed to save settings',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const renderTestButton = (providerType: string) => {
    const status = testStatus[providerType];

    return (
      <button
        type="button"
        onClick={() => handleTest(providerType)}
        disabled={status?.testing}
        className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 flex items-center gap-1"
      >
        {status?.testing ? (
          <>
            <Loader2 className="w-3 h-3 animate-spin" />
            Testing...
          </>
        ) : status?.success === true ? (
          <>
            <CheckCircle className="w-3 h-3 text-green-500" />
            Connected
          </>
        ) : status?.success === false ? (
          <>
            <XCircle className="w-3 h-3 text-red-500" />
            Failed
          </>
        ) : (
          'Test Connection'
        )}
      </button>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Configure providers and system settings
        </p>
      </div>

      <div className="space-y-6">
        {/* LLM Providers */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-cyan-100 dark:bg-cyan-900/30 rounded-lg">
              <Key className="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
            </div>
            <div>
              <h2 className="font-semibold text-gray-900 dark:text-white">LLM Providers</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Configure language model API keys and endpoints
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Ollama URL
                </label>
                {renderTestButton('ollama')}
              </div>
              <input
                type="text"
                name="ollama_url"
                value={formData.ollama_url}
                onChange={handleChange}
                placeholder="http://localhost:11434"
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm"
              />
              {testStatus.ollama?.message && (
                <p className={`mt-1 text-xs ${testStatus.ollama.success ? 'text-green-600' : 'text-red-600'}`}>
                  {testStatus.ollama.message}
                  {testStatus.ollama.latency && ` (${testStatus.ollama.latency}ms)`}
                </p>
              )}
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Anthropic API Key
                </label>
                {renderTestButton('anthropic')}
              </div>
              <input
                type="password"
                name="anthropic_api_key"
                value={formData.anthropic_api_key}
                onChange={handleChange}
                placeholder="sk-ant-..."
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm"
              />
              {testStatus.anthropic?.message && (
                <p className={`mt-1 text-xs ${testStatus.anthropic.success ? 'text-green-600' : 'text-red-600'}`}>
                  {testStatus.anthropic.message}
                </p>
              )}
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  OpenAI API Key
                </label>
                {renderTestButton('openai')}
              </div>
              <input
                type="password"
                name="openai_api_key"
                value={formData.openai_api_key}
                onChange={handleChange}
                placeholder="sk-..."
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm"
              />
              {testStatus.openai?.message && (
                <p className={`mt-1 text-xs ${testStatus.openai.success ? 'text-green-600' : 'text-red-600'}`}>
                  {testStatus.openai.message}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Voice Settings */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-pink-100 dark:bg-pink-900/30 rounded-lg">
              <Volume2 className="w-5 h-5 text-pink-600 dark:text-pink-400" />
            </div>
            <div>
              <h2 className="font-semibold text-gray-900 dark:text-white">Voice Settings</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Configure text-to-speech and speech-to-text
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  TTS Provider
                </label>
                {renderTestButton('tts')}
              </div>
              <select
                name="tts_provider"
                value={formData.tts_provider}
                onChange={handleChange}
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm"
              >
                <option value="xtts">XTTS-v2 (Local)</option>
                <option value="elevenlabs">ElevenLabs</option>
                <option value="openai">OpenAI TTS</option>
              </select>
            </div>
            {formData.tts_provider === 'xtts' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  XTTS Server URL
                </label>
                <input
                  type="text"
                  name="tts_url"
                  value={formData.tts_url}
                  onChange={handleChange}
                  placeholder="http://localhost:8020"
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm"
                />
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                STT Provider
              </label>
              <select
                name="stt_provider"
                value={formData.stt_provider}
                onChange={handleChange}
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm"
              >
                <option value="vosk">Vosk (Local)</option>
                <option value="whisper">Whisper</option>
                <option value="google">Google Speech</option>
              </select>
            </div>
          </div>
        </div>

        {/* Image Generation */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
              <Image className="w-5 h-5 text-orange-600 dark:text-orange-400" />
            </div>
            <div>
              <h2 className="font-semibold text-gray-900 dark:text-white">Image Generation</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Configure Stable Diffusion and image services
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  ComfyUI URL
                </label>
                {renderTestButton('image')}
              </div>
              <input
                type="text"
                name="comfyui_url"
                value={formData.comfyui_url}
                onChange={handleChange}
                placeholder="http://localhost:8188"
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm"
              />
              {testStatus.image?.message && (
                <p className={`mt-1 text-xs ${testStatus.image.success ? 'text-green-600' : 'text-red-600'}`}>
                  {testStatus.image.message}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Database */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg">
              <Database className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div>
              <h2 className="font-semibold text-gray-900 dark:text-white">Database</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">Database connection status</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-sm text-gray-600 dark:text-gray-300">Connected to PostgreSQL</span>
          </div>
        </div>

        {/* Save button */}
        <div className="flex items-center justify-between">
          {saveMessage && (
            <p className={`text-sm ${saveMessage.type === 'success' ? 'text-green-600' : 'text-red-600'}`}>
              {saveMessage.text}
            </p>
          )}
          <div className="flex-1" />
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {isSaving && <Loader2 className="w-4 h-4 animate-spin" />}
            {isSaving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
}

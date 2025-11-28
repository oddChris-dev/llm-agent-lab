/**
 * API service for provider management.
 */

import apiClient from './client';

export interface Provider {
  id: string;
  name: string;
  slug: string;
  type: 'llm' | 'tts' | 'stt' | 'image';
  status: 'active' | 'inactive' | 'error';
  is_default: boolean;
  is_system: boolean;
  config: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface CreateProviderData {
  name: string;
  slug: string;
  type: 'llm' | 'tts' | 'stt' | 'image';
  config: Record<string, any>;
  is_default?: boolean;
}

export interface UpdateProviderData {
  name?: string;
  config?: Record<string, any>;
  is_default?: boolean;
  status?: 'active' | 'inactive';
}

export interface TestResult {
  success: boolean;
  latency_ms: number;
  message: string;
  models: string[];
}

export interface Voice {
  id: string;
  name: string;
  language: string;
  description: string | null;
  is_cloned: boolean;
}

export interface CloneVoiceData {
  name: string;
  audio: File;
  description?: string;
}

const providersApi = {
  /**
   * List all providers, optionally filtered by type.
   */
  async listProviders(type?: string): Promise<Provider[]> {
    const params = type ? { type } : {};
    const response = await apiClient.get('/providers/', { params });
    return response.data.results || response.data;
  },

  /**
   * Get a single provider by ID.
   */
  async getProvider(id: string): Promise<Provider> {
    const response = await apiClient.get(`/providers/${id}/`);
    return response.data;
  },

  /**
   * Create a new provider.
   */
  async createProvider(data: CreateProviderData): Promise<Provider> {
    const response = await apiClient.post('/providers/', data);
    return response.data;
  },

  /**
   * Update an existing provider.
   */
  async updateProvider(id: string, data: UpdateProviderData): Promise<Provider> {
    const response = await apiClient.patch(`/providers/${id}/`, data);
    return response.data;
  },

  /**
   * Delete a provider.
   */
  async deleteProvider(id: string): Promise<void> {
    await apiClient.delete(`/providers/${id}/`);
  },

  /**
   * Test provider connection.
   */
  async testProvider(id: string): Promise<TestResult> {
    const response = await apiClient.post(`/providers/${id}/test/`);
    return response.data;
  },

  /**
   * Get available models for a provider.
   */
  async getProviderModels(id: string): Promise<string[]> {
    const response = await apiClient.get(`/providers/${id}/models/`);
    return response.data.models;
  },

  /**
   * Get available voices for a TTS provider.
   */
  async getVoices(id: string): Promise<Voice[]> {
    const response = await apiClient.get(`/providers/${id}/voices/`);
    return response.data.voices;
  },

  /**
   * Clone a voice from an audio sample.
   */
  async cloneVoice(id: string, data: CloneVoiceData): Promise<Voice> {
    const formData = new FormData();
    formData.append('name', data.name);
    formData.append('audio', data.audio);
    if (data.description) formData.append('description', data.description);

    const response = await apiClient.post(`/providers/${id}/clone_voice/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  /**
   * Delete a cloned voice.
   */
  async deleteVoice(providerId: string, voiceId: string): Promise<void> {
    await apiClient.delete(`/providers/${providerId}/voices/${voiceId}/`);
  },
};

export default providersApi;

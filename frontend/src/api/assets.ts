/**
 * API service for asset management.
 */

import apiClient from './client';

export interface Asset {
  id: string;
  name: string;
  type: 'voice_sample' | 'image' | 'audio' | 'video' | 'document' | 'other';
  type_display: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  checksum: string;
  metadata: Record<string, any>;
  usage_count: number;
  last_used_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateAssetData {
  file: File;
  name?: string;
  type: Asset['type'];
  metadata?: Record<string, any>;
}

export interface UpdateAssetData {
  name?: string;
  metadata?: Record<string, any>;
}

const assetsApi = {
  /**
   * List all assets, optionally filtered by type.
   */
  async listAssets(type?: string): Promise<Asset[]> {
    const params = type ? { type } : {};
    const response = await apiClient.get('/assets/', { params });
    return response.data.results || response.data;
  },

  /**
   * Get a single asset by ID.
   */
  async getAsset(id: string): Promise<Asset> {
    const response = await apiClient.get(`/assets/${id}/`);
    return response.data;
  },

  /**
   * Upload a new asset.
   */
  async createAsset(data: CreateAssetData): Promise<Asset> {
    const formData = new FormData();
    formData.append('file', data.file);
    formData.append('type', data.type);
    if (data.name) formData.append('name', data.name);
    if (data.metadata) formData.append('metadata', JSON.stringify(data.metadata));

    const response = await apiClient.post('/assets/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  /**
   * Update an asset.
   */
  async updateAsset(id: string, data: UpdateAssetData): Promise<Asset> {
    const response = await apiClient.patch(`/assets/${id}/`, data);
    return response.data;
  },

  /**
   * Delete an asset.
   */
  async deleteAsset(id: string): Promise<void> {
    await apiClient.delete(`/assets/${id}/`);
  },

  /**
   * Get download URL for an asset.
   */
  getDownloadUrl(id: string): string {
    return `${apiClient.defaults.baseURL}/assets/${id}/download/`;
  },
};

export default assetsApi;

/**
 * React hooks for asset management.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import assetsApi, { Asset, CreateAssetData, UpdateAssetData } from '../api/assets';

const ASSETS_KEY = 'assets';

/**
 * Hook to list all assets.
 */
export function useAssets(type?: string) {
  return useQuery({
    queryKey: [ASSETS_KEY, { type }],
    queryFn: () => assetsApi.listAssets(type),
  });
}

/**
 * Hook to get a single asset.
 */
export function useAsset(id: string | null) {
  return useQuery({
    queryKey: [ASSETS_KEY, id],
    queryFn: () => assetsApi.getAsset(id!),
    enabled: !!id,
  });
}

/**
 * Hook to upload a new asset.
 */
export function useCreateAsset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateAssetData) => assetsApi.createAsset(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ASSETS_KEY] });
    },
  });
}

/**
 * Hook to update an asset.
 */
export function useUpdateAsset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateAssetData }) =>
      assetsApi.updateAsset(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [ASSETS_KEY, variables.id] });
      queryClient.invalidateQueries({ queryKey: [ASSETS_KEY] });
    },
  });
}

/**
 * Hook to delete an asset.
 */
export function useDeleteAsset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => assetsApi.deleteAsset(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ASSETS_KEY] });
    },
  });
}

/**
 * Get the download URL for an asset.
 */
export function getAssetDownloadUrl(id: string): string {
  return assetsApi.getDownloadUrl(id);
}

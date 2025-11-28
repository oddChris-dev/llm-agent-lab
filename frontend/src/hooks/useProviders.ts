/**
 * React hooks for provider management.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import providersApi, {
  Provider,
  CreateProviderData,
  UpdateProviderData,
  TestResult,
  Voice,
  CloneVoiceData,
} from '../api/providers';

const PROVIDERS_KEY = 'providers';

/**
 * Hook to list all providers.
 */
export function useProviders(type?: string) {
  return useQuery({
    queryKey: [PROVIDERS_KEY, { type }],
    queryFn: () => providersApi.listProviders(type),
  });
}

/**
 * Hook to get a single provider.
 */
export function useProvider(id: string | null) {
  return useQuery({
    queryKey: [PROVIDERS_KEY, id],
    queryFn: () => providersApi.getProvider(id!),
    enabled: !!id,
  });
}

/**
 * Hook to create a new provider.
 */
export function useCreateProvider() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateProviderData) => providersApi.createProvider(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [PROVIDERS_KEY] });
    },
  });
}

/**
 * Hook to update a provider.
 */
export function useUpdateProvider() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateProviderData }) =>
      providersApi.updateProvider(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [PROVIDERS_KEY, variables.id] });
      queryClient.invalidateQueries({ queryKey: [PROVIDERS_KEY] });
    },
  });
}

/**
 * Hook to delete a provider.
 */
export function useDeleteProvider() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => providersApi.deleteProvider(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [PROVIDERS_KEY] });
    },
  });
}

/**
 * Hook to test a provider connection.
 */
export function useTestProvider() {
  return useMutation({
    mutationFn: (id: string) => providersApi.testProvider(id),
  });
}

/**
 * Hook to get provider models.
 */
export function useProviderModels(id: string | null) {
  return useQuery({
    queryKey: [PROVIDERS_KEY, id, 'models'],
    queryFn: () => providersApi.getProviderModels(id!),
    enabled: !!id,
  });
}

/**
 * Hook to get available voices for a TTS provider.
 */
export function useProviderVoices(id: string | null) {
  return useQuery({
    queryKey: [PROVIDERS_KEY, id, 'voices'],
    queryFn: () => providersApi.getVoices(id!),
    enabled: !!id,
  });
}

/**
 * Hook to clone a voice from an audio sample.
 */
export function useCloneVoice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ providerId, data }: { providerId: string; data: CloneVoiceData }) =>
      providersApi.cloneVoice(providerId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [PROVIDERS_KEY, variables.providerId, 'voices'] });
    },
  });
}

/**
 * Hook to delete a cloned voice.
 */
export function useDeleteVoice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ providerId, voiceId }: { providerId: string; voiceId: string }) =>
      providersApi.deleteVoice(providerId, voiceId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [PROVIDERS_KEY, variables.providerId, 'voices'] });
    },
  });
}

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { workflowsApi, WorkflowFilters } from '../api/workflows';
import type {
  Workflow,
  WorkflowDetail,
  CreateWorkflowInput,
  UpdateWorkflowInput,
} from '../types/workflow';

const WORKFLOWS_KEY = 'workflows';

export function useWorkflows(filters?: WorkflowFilters) {
  return useQuery({
    queryKey: [WORKFLOWS_KEY, filters],
    queryFn: async () => {
      const response = await workflowsApi.list(filters);
      return response.data;
    },
  });
}

export function useWorkflow(id: string | null) {
  return useQuery({
    queryKey: [WORKFLOWS_KEY, id],
    queryFn: async () => {
      if (!id) return null;
      const response = await workflowsApi.get(id);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useCreateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateWorkflowInput) => workflowsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [WORKFLOWS_KEY] });
    },
  });
}

export function useUpdateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateWorkflowInput }) =>
      workflowsApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [WORKFLOWS_KEY, variables.id] });
      queryClient.invalidateQueries({ queryKey: [WORKFLOWS_KEY] });
    },
  });
}

export function useDeleteWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => workflowsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [WORKFLOWS_KEY] });
    },
  });
}

export function useDuplicateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, name }: { id: string; name?: string }) =>
      workflowsApi.duplicate(id, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [WORKFLOWS_KEY] });
    },
  });
}

export function useExecuteWorkflow() {
  return useMutation({
    mutationFn: ({
      id,
      triggerData,
    }: {
      id: string;
      triggerData?: Record<string, unknown>;
    }) => workflowsApi.execute(id, triggerData),
  });
}

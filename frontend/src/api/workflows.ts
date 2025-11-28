import apiClient from './client';
import type { ApiResponse, PaginatedResponse } from '../types/api';
import type {
  Workflow,
  WorkflowDetail,
  CreateWorkflowInput,
  UpdateWorkflowInput,
} from '../types/workflow';

export interface WorkflowFilters {
  status?: string;
  is_template?: boolean;
  search?: string;
  page?: number;
  per_page?: number;
  ordering?: string;
}

export const workflowsApi = {
  list: async (filters?: WorkflowFilters): Promise<PaginatedResponse<Workflow>> => {
    const params = new URLSearchParams();
    if (filters?.status) params.append('status', filters.status);
    if (filters?.is_template !== undefined)
      params.append('is_template', String(filters.is_template));
    if (filters?.search) params.append('search', filters.search);
    if (filters?.page) params.append('page', String(filters.page));
    if (filters?.per_page) params.append('per_page', String(filters.per_page));
    if (filters?.ordering) params.append('ordering', filters.ordering);

    const response = await apiClient.get<PaginatedResponse<Workflow>>(
      `/workflows/?${params.toString()}`
    );
    return response.data;
  },

  get: async (id: string): Promise<ApiResponse<WorkflowDetail>> => {
    const response = await apiClient.get<ApiResponse<WorkflowDetail>>(
      `/workflows/${id}/`
    );
    return response.data;
  },

  create: async (
    data: CreateWorkflowInput
  ): Promise<ApiResponse<WorkflowDetail>> => {
    const response = await apiClient.post<ApiResponse<WorkflowDetail>>(
      '/workflows/',
      data
    );
    return response.data;
  },

  update: async (
    id: string,
    data: UpdateWorkflowInput
  ): Promise<ApiResponse<WorkflowDetail>> => {
    const response = await apiClient.patch<ApiResponse<WorkflowDetail>>(
      `/workflows/${id}/`,
      data
    );
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/workflows/${id}/`);
  },

  duplicate: async (
    id: string,
    name?: string
  ): Promise<ApiResponse<WorkflowDetail>> => {
    const response = await apiClient.post<ApiResponse<WorkflowDetail>>(
      `/workflows/${id}/duplicate/`,
      { name }
    );
    return response.data;
  },

  execute: async (
    id: string,
    triggerData?: Record<string, unknown>
  ): Promise<ApiResponse<{ id: string; status: string }>> => {
    const response = await apiClient.post<
      ApiResponse<{ id: string; status: string }>
    >(`/workflows/${id}/execute/`, { trigger_data: triggerData });
    return response.data;
  },
};

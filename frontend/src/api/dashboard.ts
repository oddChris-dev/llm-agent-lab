/**
 * API service for dashboard statistics.
 */

import apiClient from './client';

export interface DashboardStats {
  total_workflows: number;
  active_workflows: number;
  running_executions: number;
  pending_executions: number;
  queued_tasks: number;
  completed_today: number;
  failed_today: number;
}

const dashboardApi = {
  /**
   * Get dashboard statistics.
   */
  async getStats(): Promise<DashboardStats> {
    const response = await apiClient.get('/dashboard/stats/');
    return response.data;
  },
};

export default dashboardApi;

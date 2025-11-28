/**
 * React hooks for dashboard data.
 */

import { useQuery } from '@tanstack/react-query';
import dashboardApi, { DashboardStats } from '../api/dashboard';

const DASHBOARD_KEY = 'dashboard';

/**
 * Hook to get dashboard statistics.
 */
export function useDashboardStats() {
  return useQuery({
    queryKey: [DASHBOARD_KEY, 'stats'],
    queryFn: () => dashboardApi.getStats(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });
}

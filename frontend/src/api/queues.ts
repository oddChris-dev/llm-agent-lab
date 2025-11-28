/**
 * Queue API service.
 */

import apiClient from './client';

export interface Queue {
  id: string;
  name: string;
  slug: string;
  description: string;
  strategy: 'fifo' | 'lifo' | 'round_robin' | 'broadcast' | 'priority' | 'conditional';
  config: Record<string, any>;
  max_size: number | null;
  item_ttl_seconds: number | null;
  pending_count: number;
  processing_count: number;
  created_at: string;
  updated_at: string;
}

export interface QueueItem {
  id: string;
  data: any;
  priority: number;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'expired';
  attempts: number;
  max_attempts: number;
  last_error: string;
  available_at: string;
  expires_at: string | null;
  processing_started_at: string | null;
  processed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateQueueData {
  name: string;
  slug: string;
  description?: string;
  strategy?: Queue['strategy'];
  config?: Record<string, any>;
  max_size?: number;
  item_ttl_seconds?: number;
}

export interface PushItemData {
  data: any;
  priority?: number;
  delay_seconds?: number;
}

/**
 * List all queues.
 */
export async function listQueues(): Promise<Queue[]> {
  const response = await apiClient.get<{ data: Queue[] }>('/queues/');
  return response.data.data;
}

/**
 * Get a queue by ID.
 */
export async function getQueue(queueId: string): Promise<Queue> {
  const response = await apiClient.get<{ data: Queue }>(`/queues/${queueId}/`);
  return response.data.data;
}

/**
 * Create a new queue.
 */
export async function createQueue(data: CreateQueueData): Promise<Queue> {
  const response = await apiClient.post<{ data: Queue }>('/queues/', data);
  return response.data.data;
}

/**
 * Update a queue.
 */
export async function updateQueue(queueId: string, data: Partial<CreateQueueData>): Promise<Queue> {
  const response = await apiClient.patch<{ data: Queue }>(`/queues/${queueId}/`, data);
  return response.data.data;
}

/**
 * Delete a queue.
 */
export async function deleteQueue(queueId: string): Promise<void> {
  await apiClient.delete(`/queues/${queueId}/`);
}

/**
 * Push an item to a queue.
 */
export async function pushItem(queueId: string, data: PushItemData): Promise<QueueItem> {
  const response = await apiClient.post<{ data: QueueItem }>(`/queues/${queueId}/push/`, data);
  return response.data.data;
}

/**
 * Push multiple items to a queue.
 */
export async function pushBatch(queueId: string, items: PushItemData[]): Promise<QueueItem[]> {
  const response = await apiClient.post<{ data: QueueItem[] }>(`/queues/${queueId}/push_batch/`, {
    items,
  });
  return response.data.data;
}

/**
 * Pop an item from a queue.
 */
export async function popItem(
  queueId: string,
  consumerId?: string
): Promise<QueueItem | null> {
  const response = await apiClient.post<{ item: QueueItem | null }>(`/queues/${queueId}/pop/`, {
    consumer_id: consumerId,
  });
  return response.data.item;
}

/**
 * Peek at items in a queue.
 */
export async function peekItems(queueId: string, count = 5): Promise<QueueItem[]> {
  const response = await apiClient.get<{ items: QueueItem[] }>(
    `/queues/${queueId}/peek/?count=${count}`
  );
  return response.data.items;
}

/**
 * Get queue statistics.
 */
export async function getQueueStats(
  queueId: string
): Promise<{
  total: number;
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  expired: number;
  strategy: string;
  max_size: number | null;
  item_ttl_seconds: number | null;
}> {
  const response = await apiClient.get(`/queues/${queueId}/stats/`);
  return response.data;
}

/**
 * Clear items from a queue.
 */
export async function clearQueue(
  queueId: string,
  status?: QueueItem['status']
): Promise<{ cleared: number }> {
  const url = status
    ? `/queues/${queueId}/clear/?status=${status}`
    : `/queues/${queueId}/clear/`;
  const response = await apiClient.post(url);
  return response.data;
}

/**
 * Mark a queue item as completed.
 */
export async function completeItem(queueId: string, itemId: string): Promise<QueueItem> {
  const response = await apiClient.post<QueueItem>(
    `/queues/${queueId}/items/${itemId}/complete/`
  );
  return response.data;
}

/**
 * Mark a queue item as failed.
 */
export async function failItem(
  queueId: string,
  itemId: string,
  error?: string
): Promise<QueueItem> {
  const response = await apiClient.post<QueueItem>(
    `/queues/${queueId}/items/${itemId}/fail/`,
    { error }
  );
  return response.data;
}

/**
 * Requeue an item.
 */
export async function requeueItem(
  queueId: string,
  itemId: string,
  delaySeconds = 0
): Promise<QueueItem> {
  const response = await apiClient.post<QueueItem>(
    `/queues/${queueId}/items/${itemId}/requeue/`,
    { delay_seconds: delaySeconds }
  );
  return response.data;
}

export default {
  listQueues,
  getQueue,
  createQueue,
  updateQueue,
  deleteQueue,
  pushItem,
  pushBatch,
  popItem,
  peekItems,
  getQueueStats,
  clearQueue,
  completeItem,
  failItem,
  requeueItem,
};

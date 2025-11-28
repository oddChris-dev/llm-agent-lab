/**
 * React hooks for queue management.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import queuesApi, {
  Queue,
  QueueItem,
  CreateQueueData,
  UpdateQueueData,
  PushItemData,
  QueueStats,
} from '../api/queues';

const QUEUES_KEY = 'queues';
const QUEUE_ITEMS_KEY = 'queue_items';
const QUEUE_STATS_KEY = 'queue_stats';

/**
 * Hook to list all queues.
 */
export function useQueues() {
  return useQuery({
    queryKey: [QUEUES_KEY],
    queryFn: queuesApi.listQueues,
  });
}

/**
 * Hook to get a single queue by ID.
 */
export function useQueue(queueId: string | null) {
  return useQuery({
    queryKey: [QUEUES_KEY, queueId],
    queryFn: () => queuesApi.getQueue(queueId!),
    enabled: !!queueId,
  });
}

/**
 * Hook to get queue statistics.
 */
export function useQueueStats(queueId: string | null) {
  return useQuery({
    queryKey: [QUEUE_STATS_KEY, queueId],
    queryFn: () => queuesApi.getQueueStats(queueId!),
    enabled: !!queueId,
    refetchInterval: 5000, // Auto-refresh every 5 seconds
  });
}

/**
 * Hook to list items in a queue.
 */
export function useQueueItems(queueId: string | null, status?: string) {
  return useQuery({
    queryKey: [QUEUE_ITEMS_KEY, queueId, { status }],
    queryFn: () => queuesApi.listItems(queueId!, status),
    enabled: !!queueId,
  });
}

/**
 * Hook to create a new queue.
 */
export function useCreateQueue() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateQueueData) => queuesApi.createQueue(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUEUES_KEY] });
    },
  });
}

/**
 * Hook to update a queue.
 */
export function useUpdateQueue() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateQueueData }) =>
      queuesApi.updateQueue(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [QUEUES_KEY, variables.id] });
      queryClient.invalidateQueries({ queryKey: [QUEUES_KEY] });
    },
  });
}

/**
 * Hook to delete a queue.
 */
export function useDeleteQueue() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => queuesApi.deleteQueue(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUEUES_KEY] });
    },
  });
}

/**
 * Hook to push an item to a queue.
 */
export function usePushItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ queueId, data }: { queueId: string; data: PushItemData }) =>
      queuesApi.pushItem(queueId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: [QUEUE_ITEMS_KEY, variables.queueId],
      });
      queryClient.invalidateQueries({
        queryKey: [QUEUE_STATS_KEY, variables.queueId],
      });
    },
  });
}

/**
 * Hook to push multiple items to a queue.
 */
export function usePushBatch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ queueId, items }: { queueId: string; items: PushItemData[] }) =>
      queuesApi.pushBatch(queueId, items),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: [QUEUE_ITEMS_KEY, variables.queueId],
      });
      queryClient.invalidateQueries({
        queryKey: [QUEUE_STATS_KEY, variables.queueId],
      });
    },
  });
}

/**
 * Hook to pop an item from a queue.
 */
export function usePopItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ queueId, consumerId }: { queueId: string; consumerId?: string }) =>
      queuesApi.popItem(queueId, consumerId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: [QUEUE_ITEMS_KEY, variables.queueId],
      });
      queryClient.invalidateQueries({
        queryKey: [QUEUE_STATS_KEY, variables.queueId],
      });
    },
  });
}

/**
 * Hook to peek at items in a queue.
 */
export function usePeekItems(queueId: string | null, count: number = 5) {
  return useQuery({
    queryKey: [QUEUE_ITEMS_KEY, queueId, 'peek', count],
    queryFn: () => queuesApi.peekItems(queueId!, count),
    enabled: !!queueId,
  });
}

/**
 * Hook to mark a queue item as complete.
 */
export function useCompleteItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ queueId, itemId }: { queueId: string; itemId: string }) =>
      queuesApi.completeItem(queueId, itemId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: [QUEUE_ITEMS_KEY, variables.queueId],
      });
      queryClient.invalidateQueries({
        queryKey: [QUEUE_STATS_KEY, variables.queueId],
      });
    },
  });
}

/**
 * Hook to mark a queue item as failed.
 */
export function useFailItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      queueId,
      itemId,
      error,
    }: {
      queueId: string;
      itemId: string;
      error?: string;
    }) => queuesApi.failItem(queueId, itemId, error),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: [QUEUE_ITEMS_KEY, variables.queueId],
      });
      queryClient.invalidateQueries({
        queryKey: [QUEUE_STATS_KEY, variables.queueId],
      });
    },
  });
}

/**
 * Hook to requeue an item.
 */
export function useRequeueItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      queueId,
      itemId,
      delaySeconds,
    }: {
      queueId: string;
      itemId: string;
      delaySeconds?: number;
    }) => queuesApi.requeueItem(queueId, itemId, delaySeconds),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: [QUEUE_ITEMS_KEY, variables.queueId],
      });
      queryClient.invalidateQueries({
        queryKey: [QUEUE_STATS_KEY, variables.queueId],
      });
    },
  });
}

/**
 * Hook to clear items from a queue.
 */
export function useClearQueue() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ queueId, status }: { queueId: string; status?: string }) =>
      queuesApi.clearQueue(queueId, status),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: [QUEUE_ITEMS_KEY, variables.queueId],
      });
      queryClient.invalidateQueries({
        queryKey: [QUEUE_STATS_KEY, variables.queueId],
      });
    },
  });
}

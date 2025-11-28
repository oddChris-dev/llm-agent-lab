/**
 * Modal for viewing execution details, outputs, and logs.
 */

import React, { useState, useRef } from 'react';
import {
  X,
  Play,
  Pause,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Download,
  Copy,
  ChevronDown,
  ChevronRight,
  Volume2,
  FileText,
  Image as ImageIcon,
  Loader2,
} from 'lucide-react';
import {
  useExecution,
  useNodeExecutions,
  useExecutionLogs,
  usePauseExecution,
  useResumeExecution,
  useCancelExecution,
  useRetryExecution,
} from '../../hooks/useExecutions';
import type { NodeExecution, ExecutionLog } from '../../api/executions';

interface ExecutionDetailModalProps {
  executionId: string;
  onClose: () => void;
}

const STATUS_CONFIG: Record<string, { icon: React.ReactNode; color: string }> = {
  pending: { icon: <Clock className="w-4 h-4" />, color: 'text-gray-500' },
  queued: { icon: <Clock className="w-4 h-4" />, color: 'text-gray-500' },
  running: { icon: <Play className="w-4 h-4" />, color: 'text-blue-500' },
  completed: { icon: <CheckCircle className="w-4 h-4" />, color: 'text-green-500' },
  failed: { icon: <XCircle className="w-4 h-4" />, color: 'text-red-500' },
  skipped: { icon: <AlertTriangle className="w-4 h-4" />, color: 'text-gray-400' },
  paused: { icon: <Pause className="w-4 h-4" />, color: 'text-yellow-500' },
  cancelled: { icon: <AlertTriangle className="w-4 h-4" />, color: 'text-gray-400' },
};

const LOG_COLORS: Record<string, string> = {
  debug: 'text-gray-500',
  info: 'text-blue-400',
  warning: 'text-yellow-400',
  error: 'text-red-400',
};

export default function ExecutionDetailModal({
  executionId,
  onClose,
}: ExecutionDetailModalProps) {
  const [activeTab, setActiveTab] = useState<'nodes' | 'logs' | 'outputs'>('nodes');
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());

  const { data: execution, isLoading } = useExecution(executionId);
  const { data: nodeExecutions } = useNodeExecutions(executionId);
  const { data: logs } = useExecutionLogs(executionId);

  const pauseMutation = usePauseExecution();
  const resumeMutation = useResumeExecution();
  const cancelMutation = useCancelExecution();
  const retryMutation = useRetryExecution();

  const toggleNode = (nodeId: string) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  };

  if (isLoading || !execution) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        <div className="absolute inset-0 bg-black/50" onClick={onClose} />
        <div className="relative bg-white dark:bg-gray-800 rounded-lg p-8">
          <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
        </div>
      </div>
    );
  }

  const progress =
    execution.total_nodes > 0
      ? Math.round((execution.completed_nodes / execution.total_nodes) * 100)
      : 0;

  const canPause = execution.status === 'running';
  const canResume = execution.status === 'paused';
  const canCancel = ['pending', 'running', 'paused'].includes(execution.status);
  const canRetry = execution.status === 'failed';

  // Get outputs from completed nodes
  const outputNodes = nodeExecutions?.filter(
    (n) => n.status === 'completed' && n.output
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Execution Details
            </h2>
            <span
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                STATUS_CONFIG[execution.status]?.color
              } bg-gray-100 dark:bg-gray-700`}
            >
              {STATUS_CONFIG[execution.status]?.icon}
              {execution.status}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {canPause && (
              <button
                onClick={() => pauseMutation.mutate(executionId)}
                disabled={pauseMutation.isPending}
                className="px-3 py-1 text-sm bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200 disabled:opacity-50"
              >
                Pause
              </button>
            )}
            {canResume && (
              <button
                onClick={() => resumeMutation.mutate(executionId)}
                disabled={resumeMutation.isPending}
                className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200 disabled:opacity-50"
              >
                Resume
              </button>
            )}
            {canCancel && (
              <button
                onClick={() => cancelMutation.mutate(executionId)}
                disabled={cancelMutation.isPending}
                className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 disabled:opacity-50"
              >
                Cancel
              </button>
            )}
            {canRetry && (
              <button
                onClick={() => retryMutation.mutate(executionId)}
                disabled={retryMutation.isPending}
                className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50"
              >
                Retry
              </button>
            )}
            <button
              onClick={onClose}
              className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="px-6 py-3 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm text-gray-600 dark:text-gray-300">Progress</span>
            <span className="text-sm font-medium text-gray-900 dark:text-white">
              {execution.completed_nodes}/{execution.total_nodes} nodes ({progress}%)
            </span>
          </div>
          <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all ${
                execution.status === 'failed' ? 'bg-red-500' : 'bg-green-500'
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>
          {execution.failed_nodes > 0 && (
            <p className="text-xs text-red-500 mt-1">
              {execution.failed_nodes} node(s) failed
            </p>
          )}
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 dark:border-gray-700 px-6">
          <button
            onClick={() => setActiveTab('nodes')}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
              activeTab === 'nodes'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Nodes ({nodeExecutions?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('outputs')}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
              activeTab === 'outputs'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Outputs ({outputNodes?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('logs')}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
              activeTab === 'logs'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Logs ({logs?.length || 0})
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'nodes' && (
            <NodesTab
              nodeExecutions={nodeExecutions || []}
              expandedNodes={expandedNodes}
              onToggle={toggleNode}
            />
          )}
          {activeTab === 'outputs' && (
            <OutputsTab nodeExecutions={outputNodes || []} />
          )}
          {activeTab === 'logs' && <LogsTab logs={logs || []} />}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
          <div className="flex justify-between text-xs text-gray-500">
            <span>
              Started:{' '}
              {execution.started_at
                ? new Date(execution.started_at).toLocaleString()
                : 'Not started'}
            </span>
            <span>
              Completed:{' '}
              {execution.completed_at
                ? new Date(execution.completed_at).toLocaleString()
                : 'In progress'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

function NodesTab({
  nodeExecutions,
  expandedNodes,
  onToggle,
}: {
  nodeExecutions: NodeExecution[];
  expandedNodes: Set<string>;
  onToggle: (id: string) => void;
}) {
  if (nodeExecutions.length === 0) {
    return (
      <p className="text-center text-gray-500 py-8">No node executions yet</p>
    );
  }

  return (
    <div className="space-y-2">
      {nodeExecutions.map((node) => {
        const isExpanded = expandedNodes.has(node.id);
        const statusConfig = STATUS_CONFIG[node.status];

        return (
          <div
            key={node.id}
            className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
          >
            <button
              onClick={() => onToggle(node.id)}
              className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700/50"
            >
              <div className="flex items-center gap-3">
                {isExpanded ? (
                  <ChevronDown className="w-4 h-4 text-gray-400" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                )}
                <span className={statusConfig.color}>{statusConfig.icon}</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {node.node_id}
                </span>
              </div>
              <span className="text-xs text-gray-500">
                {node.duration_ms ? `${node.duration_ms}ms` : '-'}
              </span>
            </button>

            {isExpanded && (
              <div className="px-4 pb-4 space-y-3 border-t border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/30">
                {node.error_message && (
                  <div className="mt-3 p-3 bg-red-50 dark:bg-red-900/20 rounded text-sm text-red-600 dark:text-red-400">
                    {node.error_message}
                  </div>
                )}
                {node.input_data && (
                  <div className="mt-3">
                    <h4 className="text-xs font-medium text-gray-500 mb-1">Input</h4>
                    <pre className="text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded overflow-x-auto">
                      {JSON.stringify(node.input_data, null, 2)}
                    </pre>
                  </div>
                )}
                {node.output && (
                  <div>
                    <h4 className="text-xs font-medium text-gray-500 mb-1">Output</h4>
                    <pre className="text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded overflow-x-auto">
                      {JSON.stringify(node.output, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function OutputsTab({ nodeExecutions }: { nodeExecutions: NodeExecution[] }) {
  const [playingId, setPlayingId] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const handlePlay = (nodeId: string, audioData: string) => {
    if (playingId === nodeId) {
      audioRef.current?.pause();
      setPlayingId(null);
    } else {
      if (audioRef.current) {
        audioRef.current.src = `data:audio/wav;base64,${audioData}`;
        audioRef.current.play();
        setPlayingId(nodeId);
      }
    }
  };

  const handleDownload = (nodeId: string, data: any, type: string) => {
    let blob: Blob;
    let filename: string;

    if (type === 'audio' && data.audio_data) {
      const byteCharacters = atob(data.audio_data);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      blob = new Blob([new Uint8Array(byteNumbers)], { type: 'audio/wav' });
      filename = `output-${nodeId}.wav`;
    } else if (type === 'text') {
      blob = new Blob([data.text || JSON.stringify(data)], { type: 'text/plain' });
      filename = `output-${nodeId}.txt`;
    } else {
      blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      filename = `output-${nodeId}.json`;
    }

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  if (nodeExecutions.length === 0) {
    return (
      <p className="text-center text-gray-500 py-8">No outputs available yet</p>
    );
  }

  return (
    <div className="space-y-4">
      <audio
        ref={audioRef}
        onEnded={() => setPlayingId(null)}
        className="hidden"
      />

      {nodeExecutions.map((node) => {
        const output = node.output;
        const hasAudio = output?.audio_data;
        const hasText = output?.text || output?.content;
        const hasImage = output?.image_data;

        return (
          <div
            key={node.id}
            className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                {hasAudio && <Volume2 className="w-4 h-4 text-pink-500" />}
                {hasText && <FileText className="w-4 h-4 text-blue-500" />}
                {hasImage && <ImageIcon className="w-4 h-4 text-purple-500" />}
                <span className="font-medium text-gray-900 dark:text-white">
                  {node.node_id}
                </span>
              </div>
              <div className="flex items-center gap-2">
                {hasAudio && (
                  <button
                    onClick={() => handlePlay(node.id, output.audio_data)}
                    className={`p-1.5 rounded ${
                      playingId === node.id
                        ? 'bg-primary-100 text-primary-600'
                        : 'text-gray-400 hover:text-gray-600'
                    }`}
                  >
                    {playingId === node.id ? (
                      <Pause className="w-4 h-4" />
                    ) : (
                      <Play className="w-4 h-4" />
                    )}
                  </button>
                )}
                <button
                  onClick={() =>
                    handleDownload(
                      node.id,
                      output,
                      hasAudio ? 'audio' : hasText ? 'text' : 'json'
                    )
                  }
                  className="p-1.5 text-gray-400 hover:text-gray-600"
                  title="Download"
                >
                  <Download className="w-4 h-4" />
                </button>
                {hasText && (
                  <button
                    onClick={() => copyToClipboard(output.text || output.content)}
                    className="p-1.5 text-gray-400 hover:text-gray-600"
                    title="Copy to clipboard"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>

            {hasText && (
              <div className="bg-gray-50 dark:bg-gray-900/30 rounded p-3 text-sm text-gray-700 dark:text-gray-300 max-h-48 overflow-y-auto">
                {output.text || output.content}
              </div>
            )}

            {hasImage && (
              <img
                src={`data:image/png;base64,${output.image_data}`}
                alt="Output"
                className="max-w-full rounded mt-2"
              />
            )}

            {hasAudio && (
              <div className="mt-2 flex items-center gap-2 text-sm text-gray-500">
                <Volume2 className="w-4 h-4" />
                Audio output ({output.duration_ms ? `${output.duration_ms}ms` : 'unknown duration'})
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function LogsTab({ logs }: { logs: ExecutionLog[] }) {
  if (logs.length === 0) {
    return <p className="text-center text-gray-500 py-8">No logs yet</p>;
  }

  return (
    <div className="bg-gray-900 rounded-lg p-4 font-mono text-xs max-h-96 overflow-y-auto">
      {logs.map((log) => (
        <div key={log.id} className="flex gap-2 py-0.5">
          <span className="text-gray-500 shrink-0">
            {new Date(log.timestamp).toLocaleTimeString()}
          </span>
          <span className={`shrink-0 ${LOG_COLORS[log.level]}`}>
            [{log.level.toUpperCase()}]
          </span>
          {log.node_id && (
            <span className="text-purple-400 shrink-0">[{log.node_id}]</span>
          )}
          <span className="text-gray-300">{log.message}</span>
        </div>
      ))}
    </div>
  );
}

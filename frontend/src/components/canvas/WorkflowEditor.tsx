import React, { useCallback, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  BackgroundVariant,
  Panel,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Save, Play, ArrowLeft, Plus, Loader2 } from 'lucide-react';
import CustomNode from './CustomNode';
import NodeLibrary from './NodeLibrary';
import NodeConfigPanel from '../panels/NodeConfigPanel';
import ExecutionMonitor from '../execution/ExecutionMonitor';
import { useWorkflow, useUpdateWorkflow, useExecuteWorkflow } from '../../hooks/useWorkflows';

// Register custom node types
const nodeTypes = {
  custom: CustomNode,
};

export default function WorkflowEditor() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isNew = id === 'new';

  const { data: workflow, isLoading } = useWorkflow(isNew ? null : id!);
  const updateWorkflow = useUpdateWorkflow();
  const executeWorkflow = useExecuteWorkflow();

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [showLibrary, setShowLibrary] = useState(false);
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [showExecutionMonitor, setShowExecutionMonitor] = useState(false);

  // Load workflow data into React Flow state
  React.useEffect(() => {
    if (workflow) {
      const flowNodes: Node[] = workflow.nodes.map((node) => ({
        id: node.id,
        type: 'custom',
        position: node.position,
        data: {
          label: node.name || node.type.split('.')[1],
          type: node.type,
          config: node.config,
        },
      }));

      const flowEdges: Edge[] = workflow.connections.map((conn) => ({
        id: conn.id,
        source: conn.source_node_id,
        sourceHandle: conn.source_port,
        target: conn.target_node_id,
        targetHandle: conn.target_port,
        animated: true,
      }));

      setNodes(flowNodes);
      setEdges(flowEdges);
    }
  }, [workflow, setNodes, setEdges]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  const handleAddNode = useCallback(
    (type: string) => {
      const newNode: Node = {
        id: `node-${Date.now()}`,
        type: 'custom',
        position: { x: 250, y: 250 },
        data: {
          label: type.split('.')[1],
          type,
          config: {},
        },
      };
      setNodes((nds) => [...nds, newNode]);
      setShowLibrary(false);
    },
    [setNodes]
  );

  const handleSave = useCallback(async () => {
    if (!id || isNew) return;

    const nodeData = nodes.map((node) => ({
      id: node.id,
      type: node.data.type,
      name: node.data.label,
      position: node.position,
      config: node.data.config || {},
    }));

    const connectionData = edges.map((edge) => ({
      id: edge.id,
      source_node_id: edge.source,
      source_port: edge.sourceHandle || 'output',
      target_node_id: edge.target,
      target_port: edge.targetHandle || 'input',
    }));

    updateWorkflow.mutate({ id, data: { nodes: nodeData, connections: connectionData } });
  }, [id, isNew, nodes, edges, updateWorkflow]);

  const handleRun = useCallback(async () => {
    if (!id || isNew) return;

    // Save first, then execute
    const nodeData = nodes.map((node) => ({
      id: node.id,
      type: node.data.type,
      name: node.data.label,
      position: node.position,
      config: node.data.config || {},
    }));

    const connectionData = edges.map((edge) => ({
      id: edge.id,
      source_node_id: edge.source,
      source_port: edge.sourceHandle || 'output',
      target_node_id: edge.target,
      target_port: edge.targetHandle || 'input',
    }));

    // Save first
    await updateWorkflow.mutateAsync({ id, data: { nodes: nodeData, connections: connectionData } });

    // Then execute
    executeWorkflow.mutate({ id }, {
      onSuccess: (response) => {
        setExecutionId(response.data.id);
        setShowExecutionMonitor(true);
      },
    });
  }, [id, isNew, nodes, edges, updateWorkflow, executeWorkflow]);

  if (isLoading && !isNew) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
        <div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/')}
            className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="font-semibold text-gray-900 dark:text-white">
              {workflow?.name || 'New Workflow'}
            </h1>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {nodes.length} nodes, {edges.length} connections
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowLibrary(true)}
            className="inline-flex items-center gap-2 px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
          >
            <Plus className="w-4 h-4" />
            Add Node
          </button>
          <button
            onClick={handleSave}
            disabled={updateWorkflow.isPending || isNew}
            className="inline-flex items-center gap-2 px-3 py-1.5 text-sm bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {updateWorkflow.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            {updateWorkflow.isPending ? 'Saving...' : 'Save'}
          </button>
          <button
            onClick={handleRun}
            disabled={executeWorkflow.isPending || isNew}
            className="inline-flex items-center gap-2 px-3 py-1.5 text-sm bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {executeWorkflow.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            {executeWorkflow.isPending ? 'Starting...' : 'Run'}
          </button>
        </div>
      </div>

      {/* Canvas */}
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onPaneClick={onPaneClick}
          nodeTypes={nodeTypes}
          fitView
          snapToGrid
          snapGrid={[15, 15]}
        >
          <Controls />
          <MiniMap
            nodeColor={(node) => {
              const type = node.data?.type?.split('.')[0];
              const colors: Record<string, string> = {
                llm: '#06B6D4',
                voice: '#EC4899',
                web: '#14B8A6',
                queue: '#EAB308',
                image: '#F97316',
                trigger: '#8B5CF6',
                control: '#6366F1',
                output: '#22C55E',
              };
              return colors[type] || '#94A3B8';
            }}
          />
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} />

          {/* Status panel */}
          <Panel position="bottom-left" className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-2 text-xs">
            <span className="text-gray-500 dark:text-gray-400">
              Drag to pan, scroll to zoom, click node to configure
            </span>
          </Panel>
        </ReactFlow>

        {/* Node Library Modal */}
        {showLibrary && (
          <NodeLibrary
            onSelect={handleAddNode}
            onClose={() => setShowLibrary(false)}
          />
        )}

        {/* Node Config Panel */}
        {selectedNode && (
          <NodeConfigPanel
            node={selectedNode}
            onClose={() => setSelectedNode(null)}
            onUpdate={(data) => {
              setNodes((nds) =>
                nds.map((n) => (n.id === selectedNode.id ? { ...n, data } : n))
              );
            }}
          />
        )}

        {/* Execution Monitor */}
        {showExecutionMonitor && executionId && (
          <ExecutionMonitor
            executionId={executionId}
            onClose={() => {
              setShowExecutionMonitor(false);
              setExecutionId(null);
            }}
          />
        )}
      </div>
    </div>
  );
}

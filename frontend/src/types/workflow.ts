export type WorkflowStatus = 'draft' | 'active' | 'archived';

export interface Position {
  x: number;
  y: number;
}

export interface WorkflowNode {
  id: string;
  type: string;
  name: string;
  position: Position;
  width?: number;
  height?: number;
  config: Record<string, unknown>;
  inputs_config?: unknown[];
  outputs_config?: unknown[];
  created_at: string;
  updated_at: string;
}

export interface WorkflowConnection {
  id: string;
  source_node_id: string;
  source_port: string;
  target_node_id: string;
  target_port: string;
  style?: Record<string, unknown>;
  created_at: string;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  status: WorkflowStatus;
  is_template: boolean;
  node_count: number;
  connection_count: number;
  last_execution?: {
    id: string;
    status: string;
    finished_at: string | null;
  };
  created_at: string;
  updated_at: string;
}

export interface WorkflowDetail extends Workflow {
  nodes: WorkflowNode[];
  connections: WorkflowConnection[];
  canvas_data: Record<string, unknown>;
  settings: Record<string, unknown>;
  version: number;
}

export interface CreateWorkflowInput {
  name: string;
  description?: string;
  icon?: string;
  color?: string;
  status?: WorkflowStatus;
  settings?: Record<string, unknown>;
}

export interface UpdateWorkflowInput {
  name?: string;
  description?: string;
  icon?: string;
  color?: string;
  status?: WorkflowStatus;
  canvas_data?: Record<string, unknown>;
  settings?: Record<string, unknown>;
}

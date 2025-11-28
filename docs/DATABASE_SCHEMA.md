# Database Schema Design

This document defines the PostgreSQL database schema for LLM Agent Lab's workflow orchestration system.

## Design Principles

1. **Flexibility**: JSON fields for extensible configurations without schema migrations
2. **Auditability**: All important models include timestamps and soft-delete capability
3. **Performance**: Proper indexing for common query patterns
4. **Integrity**: Foreign key constraints with appropriate cascade behaviors
5. **Multi-tenancy Ready**: User ownership on all major entities

---

## Entity Relationship Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Provider    │     │    Workflow     │     │   Execution     │
│─────────────────│     │─────────────────│     │─────────────────│
│ id              │     │ id              │◀────│ workflow_id     │
│ name            │     │ name            │     │ status          │
│ type (llm/voice)│     │ description     │     │ started_at      │
│ config (JSON)   │     │ canvas_data     │     │ finished_at     │
│ is_default      │     │ is_active       │     │ context (JSON)  │
└────────┬────────┘     │ created_at      │     └────────┬────────┘
         │              │ updated_at      │              │
         │              │ user_id         │              │
         │              └────────┬────────┘              │
         │                       │                       │
         │              ┌────────┴────────┐              │
         │              │                 │              │
         │        ┌─────┴─────┐     ┌─────┴─────┐        │
         │        │   Node    │     │Connection │        │
         │        │───────────│     │───────────│        │
         │        │ id        │     │ id        │        │
         └───────▶│ type      │◀───▶│ source_id │        │
                  │ config    │     │ target_id │        │
                  │ position  │     │ source_port│       │
                  │ workflow  │     │ target_port│       │
                  └───────────┘     └───────────┘        │
                        │                                │
                        │                                │
                  ┌─────┴─────────────────────────┐      │
                  │       NodeExecution           │◀─────┘
                  │───────────────────────────────│
                  │ id                            │
                  │ node_id                       │
                  │ execution_id                  │
                  │ status                        │
                  │ input_data                    │
                  │ output_data                   │
                  │ error                         │
                  │ started_at                    │
                  │ finished_at                   │
                  └───────────────────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Queue       │     │   QueueItem     │     │     Asset       │
│─────────────────│     │─────────────────│     │─────────────────│
│ id              │◀────│ queue_id        │     │ id              │
│ name            │     │ data (JSON)     │     │ name            │
│ strategy        │     │ priority        │     │ type            │
│ workflow_id     │     │ status          │     │ file_path       │
│ config (JSON)   │     │ processed_at    │     │ metadata (JSON) │
└─────────────────┘     │ created_at      │     │ user_id         │
                        └─────────────────┘     └─────────────────┘
```

---

## Core Tables

### 1. Users (Django Auth Extended)

Uses Django's built-in User model with a profile extension.

```sql
-- Django's auth_user table is used as-is

CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER UNIQUE NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,

    -- Preferences
    default_llm_provider_id UUID REFERENCES providers(id) ON DELETE SET NULL,
    theme VARCHAR(20) DEFAULT 'system' CHECK (theme IN ('light', 'dark', 'system')),

    -- UI State
    last_workflow_id UUID REFERENCES workflows(id) ON DELETE SET NULL,
    canvas_settings JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
```

### 2. Providers

External service configurations (LLM, Voice, Image).

```sql
CREATE TYPE provider_type AS ENUM ('llm', 'voice_tts', 'voice_stt', 'image');
CREATE TYPE provider_status AS ENUM ('active', 'inactive', 'error');

CREATE TABLE providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identity
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,  -- e.g., 'anthropic', 'openai', 'ollama'
    type provider_type NOT NULL,

    -- Configuration (encrypted sensitive fields)
    config JSONB NOT NULL DEFAULT '{}',
    -- Example config for LLM:
    -- {
    --   "api_key": "encrypted:...",
    --   "base_url": "https://api.anthropic.com",
    --   "default_model": "claude-3-opus-20240229",
    --   "max_tokens": 4096,
    --   "rate_limit": 60
    -- }

    -- State
    status provider_status DEFAULT 'active',
    is_default BOOLEAN DEFAULT FALSE,
    is_system BOOLEAN DEFAULT FALSE,  -- System providers can't be deleted

    -- Ownership
    user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,  -- NULL for system providers

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_providers_default_by_type
    ON providers(user_id, type) WHERE is_default = TRUE;
CREATE INDEX idx_providers_type ON providers(type);
CREATE INDEX idx_providers_user_id ON providers(user_id);
```

### 3. Workflows

The main workflow definition containing nodes and connections.

```sql
CREATE TYPE workflow_status AS ENUM ('draft', 'active', 'archived');

CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identity
    name VARCHAR(200) NOT NULL,
    description TEXT,
    icon VARCHAR(50),  -- Emoji or icon class
    color VARCHAR(20),  -- Accent color for UI

    -- Status
    status workflow_status DEFAULT 'draft',
    is_template BOOLEAN DEFAULT FALSE,  -- Can be used as a starting point

    -- Canvas State (positions, zoom, viewport)
    canvas_data JSONB DEFAULT '{}',
    -- Example:
    -- {
    --   "viewport": {"x": 0, "y": 0, "zoom": 1},
    --   "selectedNodes": [],
    --   "minimap": true
    -- }

    -- Settings
    settings JSONB DEFAULT '{}',
    -- Example:
    -- {
    --   "autoSave": true,
    --   "executionMode": "sequential",
    --   "errorHandling": "stop_on_error"
    -- }

    -- Ownership
    user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,

    -- Versioning
    version INTEGER DEFAULT 1,
    parent_id UUID REFERENCES workflows(id) ON DELETE SET NULL,  -- For cloned workflows

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE  -- Soft delete
);

CREATE INDEX idx_workflows_user_id ON workflows(user_id);
CREATE INDEX idx_workflows_status ON workflows(status);
CREATE INDEX idx_workflows_is_template ON workflows(is_template) WHERE is_template = TRUE;
CREATE INDEX idx_workflows_deleted_at ON workflows(deleted_at) WHERE deleted_at IS NULL;
```

### 4. Nodes

Individual nodes within a workflow.

```sql
CREATE TABLE nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,

    -- Type Definition
    type VARCHAR(100) NOT NULL,  -- e.g., 'llm.claude', 'voice.tts', 'queue.fifo'

    -- Display
    name VARCHAR(200),  -- Custom name, falls back to type display name

    -- Position on Canvas
    position_x FLOAT NOT NULL DEFAULT 0,
    position_y FLOAT NOT NULL DEFAULT 0,
    width FLOAT,  -- NULL means auto-size
    height FLOAT,

    -- Configuration (type-specific)
    config JSONB NOT NULL DEFAULT '{}',
    -- Example for LLM node:
    -- {
    --   "provider_id": "uuid",
    --   "model": "claude-3-opus-20240229",
    --   "system_prompt": "You are a helpful assistant",
    --   "temperature": 0.7,
    --   "max_tokens": 4096
    -- }

    -- Input/Output Schema Override
    inputs_config JSONB DEFAULT '[]',   -- Override default inputs
    outputs_config JSONB DEFAULT '[]',  -- Override default outputs

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_nodes_workflow_id ON nodes(workflow_id);
CREATE INDEX idx_nodes_type ON nodes(type);
```

### 5. Connections

Links between node ports.

```sql
CREATE TABLE connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,

    -- Source
    source_node_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    source_port VARCHAR(100) NOT NULL,  -- e.g., 'response', 'output_1'

    -- Target
    target_node_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    target_port VARCHAR(100) NOT NULL,  -- e.g., 'prompt', 'input'

    -- Styling
    style JSONB DEFAULT '{}',
    -- Example:
    -- {
    --   "type": "smoothstep",
    --   "animated": true,
    --   "color": "#3B82F6"
    -- }

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_connection UNIQUE (source_node_id, source_port, target_node_id, target_port),
    CONSTRAINT no_self_connection CHECK (source_node_id != target_node_id)
);

CREATE INDEX idx_connections_workflow_id ON connections(workflow_id);
CREATE INDEX idx_connections_source ON connections(source_node_id);
CREATE INDEX idx_connections_target ON connections(target_node_id);
```

### 6. Queues

Reusable queue definitions for workflow control flow.

```sql
CREATE TYPE queue_strategy AS ENUM ('fifo', 'lifo', 'round_robin', 'broadcast', 'priority', 'conditional');

CREATE TABLE queues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identity
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,
    description TEXT,

    -- Behavior
    strategy queue_strategy NOT NULL DEFAULT 'fifo',
    config JSONB DEFAULT '{}',
    -- Example configs:
    -- FIFO: {"max_size": 1000, "overflow_behavior": "drop_oldest"}
    -- Round Robin: {"outputs": ["a", "b", "c"], "sticky": false}
    -- Conditional: {"conditions": [{"expr": "$.priority > 5", "output": "high"}]}
    -- Broadcast: {"outputs": ["all_subscribers"]}

    -- Limits
    max_size INTEGER,  -- NULL = unlimited
    item_ttl_seconds INTEGER,  -- NULL = no expiry

    -- Association (can be workflow-specific or global)
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,  -- NULL = global queue
    user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_queues_workflow_id ON queues(workflow_id);
CREATE INDEX idx_queues_user_id ON queues(user_id);
CREATE INDEX idx_queues_slug ON queues(slug);
```

### 7. Queue Items

Individual items in queues.

```sql
CREATE TYPE queue_item_status AS ENUM ('pending', 'processing', 'completed', 'failed', 'expired');

CREATE TABLE queue_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    queue_id UUID NOT NULL REFERENCES queues(id) ON DELETE CASCADE,

    -- Data
    data JSONB NOT NULL,

    -- Processing
    priority INTEGER DEFAULT 0,  -- Higher = processed first (for priority queue)
    status queue_item_status DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,

    -- Error Tracking
    last_error TEXT,

    -- Timing
    available_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),  -- For delayed processing
    expires_at TIMESTAMP WITH TIME ZONE,  -- Auto-expire
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processed_at TIMESTAMP WITH TIME ZONE,

    -- Provenance
    source_execution_id UUID,  -- Which execution produced this item
    source_node_id UUID,  -- Which node produced this item

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_queue_items_queue_id ON queue_items(queue_id);
CREATE INDEX idx_queue_items_status ON queue_items(status);
CREATE INDEX idx_queue_items_available ON queue_items(queue_id, status, available_at)
    WHERE status = 'pending';
CREATE INDEX idx_queue_items_priority ON queue_items(queue_id, priority DESC, created_at ASC)
    WHERE status = 'pending';
```

### 8. Executions

Workflow execution instances.

```sql
CREATE TYPE execution_status AS ENUM (
    'pending',      -- Created but not started
    'running',      -- Currently executing
    'paused',       -- Temporarily stopped
    'completed',    -- Successfully finished
    'failed',       -- Ended with error
    'cancelled'     -- Manually stopped
);

CREATE TABLE executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,

    -- Status
    status execution_status DEFAULT 'pending',

    -- Progress
    total_nodes INTEGER DEFAULT 0,
    completed_nodes INTEGER DEFAULT 0,
    failed_nodes INTEGER DEFAULT 0,

    -- Execution Context
    context JSONB DEFAULT '{}',
    -- Shared data accessible to all nodes during execution
    -- Example: {"trigger_data": {...}, "variables": {...}}

    -- Input (what triggered this execution)
    trigger_type VARCHAR(50),  -- 'manual', 'schedule', 'webhook', 'api'
    trigger_data JSONB DEFAULT '{}',

    -- Error Information
    error_message TEXT,
    error_node_id UUID,

    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE,

    -- Parent execution (for sub-workflows)
    parent_execution_id UUID REFERENCES executions(id) ON DELETE SET NULL,
    parent_node_id UUID,  -- Which node triggered this sub-execution

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_executions_workflow_id ON executions(workflow_id);
CREATE INDEX idx_executions_status ON executions(status);
CREATE INDEX idx_executions_started_at ON executions(started_at DESC);
CREATE INDEX idx_executions_parent ON executions(parent_execution_id);
```

### 9. Node Executions

Individual node execution within a workflow execution.

```sql
CREATE TYPE node_execution_status AS ENUM (
    'pending',
    'queued',
    'running',
    'completed',
    'failed',
    'skipped'
);

CREATE TABLE node_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    node_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,

    -- Status
    status node_execution_status DEFAULT 'pending',

    -- Data Flow
    input_data JSONB,
    output_data JSONB,

    -- Error Tracking
    error_message TEXT,
    error_traceback TEXT,

    -- Metrics
    retry_count INTEGER DEFAULT 0,

    -- Timing
    queued_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,  -- Computed for analytics

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_node_executions_execution_id ON node_executions(execution_id);
CREATE INDEX idx_node_executions_node_id ON node_executions(node_id);
CREATE INDEX idx_node_executions_status ON node_executions(status);
```

### 10. Execution Logs

Detailed logging for debugging and monitoring.

```sql
CREATE TYPE log_level AS ENUM ('debug', 'info', 'warning', 'error');

CREATE TABLE execution_logs (
    id BIGSERIAL PRIMARY KEY,
    execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    node_execution_id UUID REFERENCES node_executions(id) ON DELETE CASCADE,

    -- Log Entry
    level log_level DEFAULT 'info',
    message TEXT NOT NULL,
    data JSONB,  -- Additional structured data

    -- Timestamp (high precision for log ordering)
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_execution_logs_execution_id ON execution_logs(execution_id);
CREATE INDEX idx_execution_logs_timestamp ON execution_logs(timestamp DESC);
-- Partition by time for large-scale deployments
```

### 11. Assets

Stored files like voice samples, generated images, etc.

```sql
CREATE TYPE asset_type AS ENUM ('voice_sample', 'image', 'audio', 'video', 'document', 'other');

CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identity
    name VARCHAR(255) NOT NULL,
    type asset_type NOT NULL,

    -- Storage
    file_path VARCHAR(500) NOT NULL,  -- Relative path in storage
    file_size INTEGER,  -- Bytes
    mime_type VARCHAR(100),
    checksum VARCHAR(64),  -- SHA-256

    -- Metadata
    metadata JSONB DEFAULT '{}',
    -- Example for voice sample:
    -- {
    --   "duration_seconds": 6.5,
    --   "sample_rate": 22050,
    --   "channels": 1,
    --   "speaker_embedding_cached": true
    -- }

    -- Usage Tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,

    -- Ownership
    user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE  -- Soft delete
);

CREATE INDEX idx_assets_user_id ON assets(user_id);
CREATE INDEX idx_assets_type ON assets(type);
CREATE INDEX idx_assets_deleted_at ON assets(deleted_at) WHERE deleted_at IS NULL;
```

### 12. Schedules

Cron-like scheduling for workflow triggers.

```sql
CREATE TABLE schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,

    -- Schedule Definition
    name VARCHAR(200),
    cron_expression VARCHAR(100) NOT NULL,  -- e.g., '0 8 * * *' (8am daily)
    timezone VARCHAR(50) DEFAULT 'UTC',

    -- State
    is_active BOOLEAN DEFAULT TRUE,

    -- Execution Config
    trigger_data JSONB DEFAULT '{}',  -- Data passed to workflow on trigger

    -- Tracking
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    run_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_schedules_workflow_id ON schedules(workflow_id);
CREATE INDEX idx_schedules_next_run ON schedules(next_run_at) WHERE is_active = TRUE;
```

### 13. Webhooks

Webhook endpoints for triggering workflows externally.

```sql
CREATE TABLE webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,

    -- Webhook Config
    name VARCHAR(200),
    secret VARCHAR(64) NOT NULL UNIQUE,  -- Used in URL: /webhooks/{secret}

    -- Security
    is_active BOOLEAN DEFAULT TRUE,
    allowed_ips TEXT[],  -- NULL = allow all

    -- Tracking
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    trigger_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_webhooks_workflow_id ON webhooks(workflow_id);
CREATE UNIQUE INDEX idx_webhooks_secret ON webhooks(secret);
```

---

## Legacy Data Migration

Mapping from existing Flask/MySQL schema to new PostgreSQL schema:

| Old Table | New Table | Notes |
|-----------|-----------|-------|
| `agents` | `nodes` (type='llm.*') | Agents become LLM nodes with prompts in config |
| `voices` | `assets` (type='voice_sample') | Voice files stored as assets |
| `games` | `workflows` | Games become workflow templates |
| `game_variables` | `workflows.settings` | Variables stored in workflow settings JSON |
| `sessions` | `executions` | Sessions become execution runs |
| `session_players` | `nodes` + `connections` | Players become connected node chains |
| `session_settings` | `executions.context` | Settings stored in execution context |
| `session_history` | `execution_logs` | Chat history becomes execution logs |
| `transcripts` | `node_executions.output_data` | Transcripts are node outputs |
| `pages` | `node_executions.output_data` | Web pages are browser node outputs |

---

## Indexes Strategy

### Query Patterns

1. **Dashboard**: Active workflows for user → `idx_workflows_user_id`, `idx_workflows_status`
2. **Workflow Editor**: All nodes/connections for workflow → `idx_nodes_workflow_id`, `idx_connections_workflow_id`
3. **Execution Monitor**: Recent executions for workflow → `idx_executions_workflow_id`, `idx_executions_started_at`
4. **Queue Processing**: Next available items → `idx_queue_items_available`, `idx_queue_items_priority`
5. **Logging**: Logs for execution → `idx_execution_logs_execution_id`

### JSON Indexing

```sql
-- For frequently queried JSON paths
CREATE INDEX idx_nodes_provider ON nodes((config->>'provider_id'));
CREATE INDEX idx_executions_trigger ON executions(trigger_type);
```

---

## Data Retention

```sql
-- Execution logs older than 30 days
DELETE FROM execution_logs
WHERE timestamp < NOW() - INTERVAL '30 days';

-- Completed queue items older than 7 days
DELETE FROM queue_items
WHERE status IN ('completed', 'failed', 'expired')
AND processed_at < NOW() - INTERVAL '7 days';
```

---

## Security Considerations

1. **Encrypted Fields**: API keys in `providers.config` should be encrypted at rest
2. **Row-Level Security**: Consider PostgreSQL RLS for multi-tenant isolation
3. **Audit Trail**: Critical operations logged with user/timestamp
4. **Soft Deletes**: Workflows and assets use soft delete for recovery

---

*Schema Version: 1.0*
*Last Updated: 2024-01-15*

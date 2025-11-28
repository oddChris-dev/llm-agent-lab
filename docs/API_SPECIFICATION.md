# API Specification

This document defines the REST API for LLM Agent Lab. The API follows OpenAPI 3.0 specification and is designed to be self-documenting, predictable, and suitable for agent-to-agent communication.

## Base Information

- **Base URL**: `/api/v1/`
- **Authentication**: Bearer token (JWT) or API Key
- **Content-Type**: `application/json`
- **Versioning**: URL path (`/api/v1/`, `/api/v2/`)

## Authentication

### API Key Authentication
```http
Authorization: Api-Key sk-lab-xxxxxxxxxxxxx
```

### JWT Authentication
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### Obtaining Tokens
```http
POST /api/v1/auth/token/
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "secret"
}
```

**Response:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 3600
}
```

---

## Response Format

### Success Response
```json
{
  "data": { ... },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2024-01-15T14:30:00Z"
  }
}
```

### List Response
```json
{
  "data": [ ... ],
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2024-01-15T14:30:00Z",
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total_pages": 5,
      "total_count": 98
    }
  }
}
```

### Error Response
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "config.temperature",
        "message": "Must be between 0 and 2",
        "code": "out_of_range"
      }
    ]
  },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2024-01-15T14:30:00Z"
  }
}
```

### Error Codes
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `AUTHENTICATION_REQUIRED` | 401 | Missing or invalid auth token |
| `PERMISSION_DENIED` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource conflict (e.g., duplicate) |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Temporary unavailability |

---

## Endpoints

### Workflows

#### List Workflows
```http
GET /api/v1/workflows/
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status: `draft`, `active`, `archived` |
| `is_template` | boolean | Filter templates only |
| `search` | string | Search by name/description |
| `ordering` | string | Sort: `created_at`, `-created_at`, `name`, `-updated_at` |
| `page` | integer | Page number (default: 1) |
| `per_page` | integer | Items per page (default: 20, max: 100) |

**Response:**
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Custom Radio Show",
      "description": "Generates personalized radio segments",
      "icon": "📻",
      "color": "#3B82F6",
      "status": "active",
      "is_template": false,
      "node_count": 12,
      "connection_count": 15,
      "last_execution": {
        "id": "660e8400-e29b-41d4-a716-446655440000",
        "status": "completed",
        "finished_at": "2024-01-15T14:25:00Z"
      },
      "created_at": "2024-01-10T10:00:00Z",
      "updated_at": "2024-01-15T14:30:00Z"
    }
  ],
  "meta": {
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total_pages": 1,
      "total_count": 5
    }
  }
}
```

#### Create Workflow
```http
POST /api/v1/workflows/
```

**Request Body:**
```json
{
  "name": "My New Workflow",
  "description": "Description of what this workflow does",
  "icon": "🤖",
  "color": "#10B981",
  "status": "draft",
  "settings": {
    "auto_save": true,
    "execution_mode": "sequential",
    "error_handling": "stop_on_error"
  }
}
```

**Response:** `201 Created`
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "My New Workflow",
    "description": "Description of what this workflow does",
    "icon": "🤖",
    "color": "#10B981",
    "status": "draft",
    "is_template": false,
    "nodes": [],
    "connections": [],
    "canvas_data": {
      "viewport": {"x": 0, "y": 0, "zoom": 1}
    },
    "settings": {
      "auto_save": true,
      "execution_mode": "sequential",
      "error_handling": "stop_on_error"
    },
    "created_at": "2024-01-15T14:30:00Z",
    "updated_at": "2024-01-15T14:30:00Z"
  }
}
```

#### Get Workflow (Full Detail)
```http
GET /api/v1/workflows/{id}/
```

**Response:**
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Custom Radio Show",
    "description": "Generates personalized radio segments",
    "icon": "📻",
    "color": "#3B82F6",
    "status": "active",
    "is_template": false,
    "nodes": [
      {
        "id": "node-1",
        "type": "trigger.browser_watch",
        "name": "Browser Watcher",
        "position": {"x": 100, "y": 100},
        "config": {
          "url_patterns": ["*.news.*", "*.reddit.com/*"]
        },
        "inputs": [],
        "outputs": [
          {"id": "page", "type": "object", "label": "Page Data"}
        ]
      },
      {
        "id": "node-2",
        "type": "llm.claude",
        "name": "Topic Analyzer",
        "position": {"x": 350, "y": 100},
        "config": {
          "provider_id": "provider-anthropic-1",
          "model": "claude-3-opus-20240229",
          "system_prompt": "Analyze the page and extract key topics...",
          "temperature": 0.3,
          "max_tokens": 1024
        },
        "inputs": [
          {"id": "prompt", "type": "string", "label": "Prompt", "required": true},
          {"id": "context", "type": "string", "label": "Context"}
        ],
        "outputs": [
          {"id": "response", "type": "string", "label": "Response"}
        ]
      }
    ],
    "connections": [
      {
        "id": "conn-1",
        "source_node_id": "node-1",
        "source_port": "page",
        "target_node_id": "node-2",
        "target_port": "prompt"
      }
    ],
    "canvas_data": {
      "viewport": {"x": 0, "y": 0, "zoom": 1},
      "minimap": true
    },
    "settings": {
      "auto_save": true,
      "execution_mode": "sequential"
    },
    "version": 3,
    "created_at": "2024-01-10T10:00:00Z",
    "updated_at": "2024-01-15T14:30:00Z"
  }
}
```

#### Update Workflow
```http
PUT /api/v1/workflows/{id}/
PATCH /api/v1/workflows/{id}/
```

**Request Body (PATCH - partial update):**
```json
{
  "name": "Updated Workflow Name",
  "status": "active"
}
```

#### Delete Workflow
```http
DELETE /api/v1/workflows/{id}/
```

**Response:** `204 No Content`

#### Duplicate Workflow
```http
POST /api/v1/workflows/{id}/duplicate/
```

**Request Body:**
```json
{
  "name": "Copy of Custom Radio Show"
}
```

**Response:** `201 Created` (new workflow object)

---

### Nodes

#### Add Node to Workflow
```http
POST /api/v1/workflows/{workflow_id}/nodes/
```

**Request Body:**
```json
{
  "type": "llm.claude",
  "name": "Content Generator",
  "position": {"x": 200, "y": 150},
  "config": {
    "provider_id": "550e8400-e29b-41d4-a716-446655440000",
    "model": "claude-3-opus-20240229",
    "system_prompt": "You are a creative content generator...",
    "temperature": 0.7,
    "max_tokens": 2048
  }
}
```

#### Update Node
```http
PATCH /api/v1/workflows/{workflow_id}/nodes/{node_id}/
```

**Request Body:**
```json
{
  "position": {"x": 250, "y": 175},
  "config": {
    "temperature": 0.5
  }
}
```

#### Delete Node
```http
DELETE /api/v1/workflows/{workflow_id}/nodes/{node_id}/
```

**Note:** Deleting a node also removes all connections to/from it.

#### Batch Update Nodes (for canvas operations)
```http
PATCH /api/v1/workflows/{workflow_id}/nodes/batch/
```

**Request Body:**
```json
{
  "updates": [
    {"id": "node-1", "position": {"x": 100, "y": 100}},
    {"id": "node-2", "position": {"x": 350, "y": 100}},
    {"id": "node-3", "position": {"x": 600, "y": 100}}
  ]
}
```

---

### Connections

#### Add Connection
```http
POST /api/v1/workflows/{workflow_id}/connections/
```

**Request Body:**
```json
{
  "source_node_id": "node-1",
  "source_port": "response",
  "target_node_id": "node-2",
  "target_port": "prompt"
}
```

#### Delete Connection
```http
DELETE /api/v1/workflows/{workflow_id}/connections/{connection_id}/
```

---

### Node Types

#### List Available Node Types
```http
GET /api/v1/node-types/
```

**Response:**
```json
{
  "data": [
    {
      "type": "llm.claude",
      "category": "llm",
      "name": "Claude",
      "description": "Anthropic Claude language model",
      "icon": "🤖",
      "color": "#06B6D4",
      "inputs": [
        {
          "id": "prompt",
          "type": "string",
          "label": "Prompt",
          "required": true,
          "description": "The input prompt for the model"
        },
        {
          "id": "context",
          "type": "string",
          "label": "Context",
          "required": false
        },
        {
          "id": "images",
          "type": "array",
          "label": "Images",
          "required": false,
          "description": "Images for vision models"
        }
      ],
      "outputs": [
        {
          "id": "response",
          "type": "string",
          "label": "Response"
        },
        {
          "id": "usage",
          "type": "object",
          "label": "Usage Metadata"
        }
      ],
      "config_schema": {
        "type": "object",
        "properties": {
          "provider_id": {"type": "string", "format": "uuid"},
          "model": {"type": "string", "default": "claude-3-opus-20240229"},
          "system_prompt": {"type": "string"},
          "temperature": {"type": "number", "minimum": 0, "maximum": 2, "default": 0.7},
          "max_tokens": {"type": "integer", "minimum": 1, "maximum": 100000, "default": 4096}
        },
        "required": ["provider_id"]
      }
    },
    {
      "type": "queue.fifo",
      "category": "queue",
      "name": "FIFO Queue",
      "description": "First-in, first-out queue",
      "icon": "📋",
      "color": "#EAB308",
      "inputs": [
        {"id": "input", "type": "any", "label": "Input"}
      ],
      "outputs": [
        {"id": "output", "type": "any", "label": "Output"}
      ],
      "config_schema": {
        "type": "object",
        "properties": {
          "max_size": {"type": "integer", "default": 1000},
          "overflow_behavior": {
            "type": "string",
            "enum": ["drop_oldest", "drop_newest", "block"],
            "default": "drop_oldest"
          }
        }
      }
    }
  ]
}
```

---

### Executions

#### Start Execution
```http
POST /api/v1/workflows/{workflow_id}/execute/
```

**Request Body:**
```json
{
  "trigger_data": {
    "topic": "artificial intelligence trends",
    "depth": "comprehensive"
  }
}
```

**Response:** `202 Accepted`
```json
{
  "data": {
    "id": "exec-550e8400-e29b-41d4-a716-446655440000",
    "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "trigger_type": "api",
    "trigger_data": {
      "topic": "artificial intelligence trends",
      "depth": "comprehensive"
    },
    "created_at": "2024-01-15T14:30:00Z"
  }
}
```

#### List Executions
```http
GET /api/v1/executions/
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `workflow_id` | uuid | Filter by workflow |
| `status` | string | Filter by status |
| `started_after` | datetime | Filter by start time |
| `started_before` | datetime | Filter by start time |

#### Get Execution Details
```http
GET /api/v1/executions/{id}/
```

**Response:**
```json
{
  "data": {
    "id": "exec-550e8400",
    "workflow_id": "550e8400",
    "workflow_name": "Custom Radio Show",
    "status": "running",
    "progress": {
      "total_nodes": 12,
      "completed_nodes": 7,
      "failed_nodes": 0,
      "percentage": 58
    },
    "trigger_type": "api",
    "trigger_data": {"topic": "AI trends"},
    "context": {
      "variables": {
        "current_topic": "Machine Learning Advances"
      }
    },
    "started_at": "2024-01-15T14:30:00Z",
    "node_executions": [
      {
        "id": "ne-1",
        "node_id": "node-1",
        "node_name": "Browser Watcher",
        "node_type": "trigger.browser_watch",
        "status": "completed",
        "started_at": "2024-01-15T14:30:00Z",
        "finished_at": "2024-01-15T14:30:05Z",
        "duration_ms": 5000
      },
      {
        "id": "ne-2",
        "node_id": "node-2",
        "node_name": "Topic Analyzer",
        "node_type": "llm.claude",
        "status": "running",
        "started_at": "2024-01-15T14:30:06Z"
      }
    ],
    "created_at": "2024-01-15T14:30:00Z"
  }
}
```

#### Get Execution Logs
```http
GET /api/v1/executions/{id}/logs/
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `level` | string | Filter: `debug`, `info`, `warning`, `error` |
| `node_id` | uuid | Filter by specific node |
| `since` | datetime | Logs after timestamp |
| `limit` | integer | Max logs to return (default: 100) |

**Response:**
```json
{
  "data": [
    {
      "id": 12345,
      "level": "info",
      "message": "Starting workflow execution",
      "node_id": null,
      "node_name": null,
      "data": {"trigger": "api"},
      "timestamp": "2024-01-15T14:30:00.000Z"
    },
    {
      "id": 12346,
      "level": "info",
      "message": "Node started",
      "node_id": "node-1",
      "node_name": "Browser Watcher",
      "data": null,
      "timestamp": "2024-01-15T14:30:00.100Z"
    },
    {
      "id": 12347,
      "level": "debug",
      "message": "Detected URL change",
      "node_id": "node-1",
      "node_name": "Browser Watcher",
      "data": {"url": "https://news.ycombinator.com/"},
      "timestamp": "2024-01-15T14:30:02.500Z"
    }
  ]
}
```

#### Pause Execution
```http
POST /api/v1/executions/{id}/pause/
```

#### Resume Execution
```http
POST /api/v1/executions/{id}/resume/
```

#### Cancel Execution
```http
POST /api/v1/executions/{id}/cancel/
```

---

### Queues

#### List Queues
```http
GET /api/v1/queues/
```

#### Create Queue
```http
POST /api/v1/queues/
```

**Request Body:**
```json
{
  "name": "Topic Processing Queue",
  "slug": "topic-queue",
  "strategy": "fifo",
  "config": {
    "max_size": 1000,
    "overflow_behavior": "drop_oldest"
  },
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Get Queue Status
```http
GET /api/v1/queues/{id}/
```

**Response:**
```json
{
  "data": {
    "id": "queue-550e8400",
    "name": "Topic Processing Queue",
    "slug": "topic-queue",
    "strategy": "fifo",
    "config": {
      "max_size": 1000
    },
    "stats": {
      "pending": 47,
      "processing": 2,
      "completed_today": 156,
      "failed_today": 3,
      "average_processing_time_ms": 2500
    },
    "created_at": "2024-01-10T10:00:00Z"
  }
}
```

#### Enqueue Item
```http
POST /api/v1/queues/{id}/items/
```

**Request Body:**
```json
{
  "data": {
    "topic": "Quantum Computing",
    "source": "manual"
  },
  "priority": 5
}
```

#### Dequeue Item (for manual consumers)
```http
POST /api/v1/queues/{id}/dequeue/
```

#### List Queue Items
```http
GET /api/v1/queues/{id}/items/
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter: `pending`, `processing`, `completed`, `failed` |

---

### Providers

#### List Providers
```http
GET /api/v1/providers/
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | Filter: `llm`, `voice_tts`, `voice_stt`, `image` |

**Response:**
```json
{
  "data": [
    {
      "id": "provider-anthropic-1",
      "name": "Anthropic",
      "slug": "anthropic",
      "type": "llm",
      "status": "active",
      "is_default": true,
      "available_models": [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-5-sonnet-20241022"
      ],
      "config": {
        "base_url": "https://api.anthropic.com",
        "default_model": "claude-3-opus-20240229",
        "max_tokens": 4096
      },
      "created_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": "provider-ollama-1",
      "name": "Ollama (Local)",
      "slug": "ollama",
      "type": "llm",
      "status": "active",
      "is_default": false,
      "available_models": [
        "llama3.1:70b",
        "llama3.1:8b",
        "codellama:34b"
      ],
      "config": {
        "base_url": "http://localhost:11434",
        "default_model": "llama3.1:70b"
      },
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### Create Provider
```http
POST /api/v1/providers/
```

**Request Body:**
```json
{
  "name": "OpenAI",
  "slug": "openai",
  "type": "llm",
  "config": {
    "api_key": "sk-...",
    "base_url": "https://api.openai.com/v1",
    "default_model": "gpt-4-turbo",
    "max_tokens": 4096
  },
  "is_default": false
}
```

#### Test Provider Connection
```http
POST /api/v1/providers/{id}/test/
```

**Response:**
```json
{
  "data": {
    "success": true,
    "latency_ms": 245,
    "available_models": ["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
    "rate_limits": {
      "requests_per_minute": 60,
      "tokens_per_minute": 90000
    }
  }
}
```

---

### Assets

#### List Assets
```http
GET /api/v1/assets/
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | Filter: `voice_sample`, `image`, `audio`, `video` |

#### Upload Asset
```http
POST /api/v1/assets/
Content-Type: multipart/form-data
```

**Form Data:**
| Field | Type | Description |
|-------|------|-------------|
| `file` | file | The file to upload |
| `name` | string | Display name |
| `type` | string | Asset type |
| `metadata` | json | Optional metadata |

#### Get Asset
```http
GET /api/v1/assets/{id}/
```

#### Download Asset File
```http
GET /api/v1/assets/{id}/download/
```

---

### Webhooks

#### Create Webhook
```http
POST /api/v1/workflows/{workflow_id}/webhooks/
```

**Request Body:**
```json
{
  "name": "GitHub Push Handler"
}
```

**Response:**
```json
{
  "data": {
    "id": "webhook-550e8400",
    "name": "GitHub Push Handler",
    "secret": "whk_a1b2c3d4e5f6g7h8i9j0",
    "url": "https://yourdomain.com/api/v1/webhooks/whk_a1b2c3d4e5f6g7h8i9j0/",
    "is_active": true,
    "created_at": "2024-01-15T14:30:00Z"
  }
}
```

#### Trigger Webhook
```http
POST /api/v1/webhooks/{secret}/
```

**Request Body:** (any JSON - passed as trigger_data)
```json
{
  "event": "push",
  "repository": "myrepo",
  "commit": "abc123"
}
```

---

### Real-time Updates (WebSocket)

#### Execution Updates
```
WS /ws/executions/{execution_id}/
```

**Messages from Server:**
```json
{
  "type": "execution_update",
  "data": {
    "status": "running",
    "progress": {"completed_nodes": 5, "total_nodes": 12}
  }
}
```

```json
{
  "type": "node_update",
  "data": {
    "node_id": "node-2",
    "status": "completed",
    "output_data": {"response": "..."}
  }
}
```

```json
{
  "type": "log",
  "data": {
    "level": "info",
    "message": "Processing complete",
    "node_id": "node-2"
  }
}
```

#### Workflow Canvas Sync (for collaboration)
```
WS /ws/workflows/{workflow_id}/
```

**Messages:**
```json
{
  "type": "node_moved",
  "data": {
    "node_id": "node-1",
    "position": {"x": 150, "y": 200},
    "user_id": 123
  }
}
```

---

## Rate Limiting

| Endpoint Pattern | Rate Limit |
|-----------------|------------|
| `POST /api/v1/auth/*` | 5/minute |
| `POST /api/v1/*/execute/` | 10/minute |
| `GET /api/v1/*` | 100/minute |
| `POST/PUT/PATCH /api/v1/*` | 60/minute |
| `WS /*` | 5 connections/user |

Rate limit headers:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705329600
```

---

## Pagination

All list endpoints support pagination:

```http
GET /api/v1/workflows/?page=2&per_page=50
```

Response includes pagination metadata:
```json
{
  "meta": {
    "pagination": {
      "page": 2,
      "per_page": 50,
      "total_pages": 10,
      "total_count": 487,
      "has_next": true,
      "has_prev": true
    }
  }
}
```

---

## Filtering & Sorting

### Filtering
```http
GET /api/v1/executions/?status=running&workflow_id=550e8400-...
```

### Sorting
```http
GET /api/v1/workflows/?ordering=-updated_at
GET /api/v1/workflows/?ordering=name,-created_at
```

Prefix `-` for descending order.

---

## API Versioning Strategy

- **URL Path Versioning**: `/api/v1/`, `/api/v2/`
- **Deprecation**: Old versions supported for 12 months
- **Headers**: `X-API-Version: 1.0.0` in responses

---

## SDK Examples

### Python
```python
from agent_lab import AgentLabClient

client = AgentLabClient(
    base_url="https://your-instance.com",
    api_key="sk-lab-xxxxx"
)

# Create and run a workflow
workflow = client.workflows.create(
    name="My Workflow",
    status="active"
)

node1 = workflow.add_node(
    type="trigger.manual",
    position={"x": 100, "y": 100}
)

node2 = workflow.add_node(
    type="llm.claude",
    position={"x": 350, "y": 100},
    config={
        "model": "claude-3-opus-20240229",
        "system_prompt": "You are helpful"
    }
)

workflow.connect(node1, "output", node2, "prompt")
workflow.save()

# Execute
execution = workflow.execute(trigger_data={"input": "Hello!"})

# Monitor
for event in execution.stream():
    print(f"{event.type}: {event.data}")
```

### JavaScript/TypeScript
```typescript
import { AgentLabClient } from '@agent-lab/sdk';

const client = new AgentLabClient({
  baseUrl: 'https://your-instance.com',
  apiKey: 'sk-lab-xxxxx'
});

// Create workflow
const workflow = await client.workflows.create({
  name: 'My Workflow',
  status: 'active'
});

// Add nodes
const node1 = await workflow.addNode({
  type: 'trigger.manual',
  position: { x: 100, y: 100 }
});

// Execute and stream updates
const execution = await workflow.execute({ input: 'Hello!' });

for await (const event of execution.stream()) {
  console.log(`${event.type}:`, event.data);
}
```

---

## Agent-to-Agent Workflow Example

A workflow can programmatically create and manage other workflows:

```python
# Inside a "Meta Agent" workflow's custom node:

def execute(self, input_data, context, client):
    """Create a specialized workflow based on user request."""

    user_request = input_data["request"]

    # Analyze what kind of workflow is needed
    analysis = client.llm.generate(
        model="claude-3-opus-20240229",
        prompt=f"Analyze this request and suggest workflow nodes: {user_request}"
    )

    # Create new workflow programmatically
    new_workflow = client.workflows.create(
        name=f"Auto-generated: {user_request[:50]}",
        status="active"
    )

    # Add nodes based on analysis
    for node_spec in analysis["suggested_nodes"]:
        new_workflow.add_node(**node_spec)

    # Connect nodes
    for conn_spec in analysis["connections"]:
        new_workflow.connect(**conn_spec)

    # Start execution
    execution = new_workflow.execute()

    return {
        "workflow_id": new_workflow.id,
        "execution_id": execution.id,
        "status": "created_and_started"
    }
```

---

*API Version: 1.0*
*Last Updated: 2024-01-15*

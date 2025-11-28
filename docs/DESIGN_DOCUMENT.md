# LLM Agent Lab - Design Document

## Vision

**LLM Agent Lab** is a visual workflow orchestration platform for AI agents. It enables users to design, build, and execute complex multi-agent workflows through an intuitive drag-and-drop interface. The platform supports multiple LLM providers, various I/O modalities (text, voice, vision, web), and collaborative execution across distributed systems.

### Core Principles

1. **Visual-First**: Workflows are designed visually as node graphs, making complex agent orchestration accessible
2. **Modular & Extensible**: Every capability is a pluggable node type, easy to add new integrations
3. **API-Driven**: The entire system is controllable via REST API, enabling agent-to-agent workflow management
4. **Pleasant Developer Experience**: Hot reload, clear documentation, comprehensive testing
5. **Flexible Execution**: Workflows can be long-running, distributed, and resumable

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React + TypeScript)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Workflow   │  │   Node      │  │  Execution  │  │     Settings &      │ │
│  │  Canvas     │  │   Library   │  │   Monitor   │  │     Management      │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │ REST API / WebSocket
┌────────────────────────────────┴────────────────────────────────────────────┐
│                           BACKEND (Django REST Framework)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Workflow   │  │   Queue     │  │  Execution  │  │     Provider        │ │
│  │  Service    │  │   Manager   │  │   Engine    │  │     Registry        │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Voice     │  │   Browser   │  │   Image     │  │     LLM             │ │
│  │   Service   │  │   Service   │  │   Service   │  │     Service         │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
┌────────────────────────────────┴────────────────────────────────────────────┐
│                           DATABASE (PostgreSQL)                              │
│  Workflows │ Nodes │ Connections │ Queues │ Executions │ Providers │ Assets │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## UX Design

### 1. Workflow Canvas

The heart of the application is a visual canvas where users build agent workflows.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ◀ Workflows    │    Custom Radio Show v2.3    │  ▶ Run  ⏸ Pause  💾 Save   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────┐                                                             │
│  │ 🎤 Voice   │──┐                              ┌────────────┐              │
│  │   Input    │  │    ┌────────────┐            │ 🔊 Voice   │              │
│  └────────────┘  └───▶│ 🤖 Claude  │──────────▶│   Output   │              │
│                       │  Analyzer  │            └────────────┘              │
│  ┌────────────┐  ┌───▶│            │                                        │
│  │ 🌐 Browser │──┘    └────────────┘                                        │
│  │   Watcher  │              │                                              │
│  └────────────┘              ▼                                              │
│                       ┌────────────┐            ┌────────────┐              │
│                       │ 📋 FIFO    │───────────▶│ 🔍 Web     │              │
│                       │   Queue    │            │   Search   │              │
│                       └────────────┘            └────────────┘              │
│                                                        │                    │
│                                                        ▼                    │
│                                                 ┌────────────┐              │
│                                                 │ 📝 Script  │              │
│                                                 │  Generator │              │
│                                                 └────────────┘              │
│                                                        │                    │
│  ┌─────────────────────────────────────────────────────┼───────────────┐    │
│  │ Node Library                                        ▼               │    │
│  │ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐  ┌────────────┐          │    │
│  │ │ 🤖 │ │ 🌐 │ │ 🔊 │ │ 🎤 │ │ 🖼️ │ │ 📋 │  │ 📻 Radio   │          │    │
│  │ │LLM │ │Web │ │TTS │ │STT │ │Img │ │Queue│  │   Show     │          │    │
│  │ └────┘ └────┘ └────┘ └────┘ └────┘ └────┘  └────────────┘          │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Canvas Features

- **Drag & Drop Nodes**: Pull nodes from the library onto the canvas
- **Connection Wires**: Click and drag from output port to input port
- **Pan & Zoom**: Navigate large workflows smoothly
- **Mini-map**: Overview of entire workflow for quick navigation
- **Snap-to-Grid**: Optional alignment for clean layouts
- **Multi-select**: Box select or Ctrl+click to select multiple nodes
- **Copy/Paste**: Duplicate node groups within or across workflows
- **Undo/Redo**: Full history support with Ctrl+Z/Ctrl+Y
- **Real-time Collaboration**: See other users' cursors (future enhancement)

### 2. Node Types

Each node has a consistent visual structure:

```
┌─────────────────────────────────────┐
│  🤖 Claude 3.5 Sonnet              │  ← Header with icon & name
├─────────────────────────────────────┤
│  ○ prompt         response ●        │  ← Input/output ports
│  ○ context                          │
│  ○ temperature                      │
├─────────────────────────────────────┤
│  Model: claude-3-5-sonnet           │  ← Quick config preview
│  Tokens: 4096                       │
│  [⚙️ Configure]                     │  ← Open settings panel
└─────────────────────────────────────┘
```

#### Node Categories

| Category | Nodes | Purpose |
|----------|-------|---------|
| **Triggers** | Schedule, Webhook, Manual, Browser Watch | Start workflow execution |
| **LLM** | Claude, GPT, Ollama, Custom | Text generation and reasoning |
| **Voice** | TTS, STT, Voice Clone | Audio input/output |
| **Web** | Search, Fetch, Screenshot, Browser | Internet interaction |
| **Image** | Generate, Edit, Analyze, ComfyUI | Visual content |
| **Data** | Transform, Filter, Merge, Split | Data manipulation |
| **Queue** | FIFO, Round Robin, Broadcast, Conditional | Flow control |
| **Storage** | Database, File, Memory, Cache | Persistence |
| **Control** | Condition, Loop, Delay, Parallel | Logic flow |
| **Output** | Display, Notify, Save, API Call | Results delivery |

### 3. Node Configuration Panel

When a node is selected, a side panel opens with detailed configuration:

```
┌─────────────────────────────────────┐
│  🤖 Claude 3.5 Sonnet    [×]        │
├─────────────────────────────────────┤
│  GENERAL                            │
│  ────────────────────               │
│  Name: [Topic Analyzer________]     │
│  Description: [Analyzes topics_]    │
│                                     │
│  PROVIDER                           │
│  ────────────────────               │
│  Provider: [Anthropic     ▼]        │
│  Model:    [claude-3-5-sonnet ▼]    │
│  API Key:  [Use default   ▼]        │
│                                     │
│  PARAMETERS                         │
│  ────────────────────               │
│  Max Tokens: [4096______]           │
│  Temperature: [0.7] ──●────         │
│  System Prompt:                     │
│  ┌───────────────────────────────┐  │
│  │ You are a topic analyzer...   │  │
│  │                               │  │
│  └───────────────────────────────┘  │
│                                     │
│  INPUTS                             │
│  ────────────────────               │
│  ☑ prompt (required)                │
│  ☑ context (optional)               │
│  ☐ images (optional)                │
│                                     │
│  OUTPUTS                            │
│  ────────────────────               │
│  ☑ response (text)                  │
│  ☐ usage (metadata)                 │
│                                     │
│  [Test Node] [Apply] [Cancel]       │
└─────────────────────────────────────┘
```

### 4. Queue Node Types

Queues are a special category that control how data flows between nodes:

#### FIFO Queue
```
Items processed in order received
┌─────────────────────────────────┐
│  📋 FIFO Queue                  │
│  ○ input         output ●       │
│  ────────────────────────       │
│  [A] → [B] → [C] → [D] → ...   │
│  Max: 1000 | Current: 47        │
└─────────────────────────────────┘
```

#### Round Robin (Distribute)
```
Distributes items across outputs
┌─────────────────────────────────┐
│  🔄 Round Robin                 │
│  ○ input         output_1 ●     │
│                  output_2 ●     │
│                  output_3 ●     │
│  ────────────────────────       │
│  Next: output_2 | Sent: 156     │
└─────────────────────────────────┘
```

#### Broadcast (Repeat)
```
Sends each item to ALL outputs
┌─────────────────────────────────┐
│  📢 Broadcast                   │
│  ○ input         output_1 ●     │
│                  output_2 ●     │
│                  output_3 ●     │
│  ────────────────────────       │
│  Sent to all: 89 items          │
└─────────────────────────────────┘
```

#### Conditional Router
```
Routes based on conditions
┌─────────────────────────────────┐
│  🔀 Conditional                 │
│  ○ input         if_true ●      │
│                  if_false ●     │
│  ────────────────────────       │
│  Condition: {{length > 100}}    │
│  True: 45 | False: 23           │
└─────────────────────────────────┘
```

### 5. Execution Monitor

Real-time view of workflow execution:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Execution Monitor                                     [↻ Refresh] [⏸ Pause] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Run #1247 - Custom Radio Show                                              │
│  Started: 2024-01-15 14:23:45 | Duration: 00:15:32 | Status: 🟢 Running    │
│                                                                             │
│  ┌─ Node Execution Log ───────────────────────────────────────────────────┐ │
│  │ 14:23:45 ▶ Browser Watcher        Watching user navigation...          │ │
│  │ 14:24:12 ✓ Browser Watcher        Detected: news.ycombinator.com       │ │
│  │ 14:24:13 ▶ Topic Analyzer         Processing page content...           │ │
│  │ 14:24:18 ✓ Topic Analyzer         Topics: [AI, Robotics, Startups]     │ │
│  │ 14:24:19 ▶ FIFO Queue             Enqueued 3 topics                    │ │
│  │ 14:24:19 ▶ Web Search             Searching: "AI robotics 2024"        │ │
│  │ 14:24:25 ✓ Web Search             Found 15 results                     │ │
│  │ 14:24:26 ▶ Script Generator       Generating radio segment...          │ │
│  │ 14:24:45 ✓ Script Generator       Script ready (2,450 words)           │ │
│  │ 14:24:46 ▶ Voice Output           Speaking segment 1/5...              │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─ Queue Status ──────────────────┐  ┌─ Resource Usage ─────────────────┐ │
│  │ Topics Queue:     12 pending    │  │ CPU: ███████░░░ 68%              │ │
│  │ Scripts Queue:     3 pending    │  │ GPU: █████████░ 89%              │ │
│  │ Voice Queue:       7 pending    │  │ RAM: ████░░░░░░ 41%              │ │
│  └─────────────────────────────────┘  └──────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6. Dashboard

Main landing page showing all workflows and system status:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🔬 LLM Agent Lab                              🔔 │ ⚙️ │ 👤 Chris          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─ Quick Stats ────────────────────────────────────────────────────────┐  │
│  │  📊 12 Workflows  │  🟢 3 Running  │  📋 47 Queued  │  ✓ 1,234 Today │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─ My Workflows ───────────────────────────────────────────────────────┐  │
│  │                                                        [+ New Workflow] │
│  │  ┌──────────────────────┐  ┌──────────────────────┐  ┌────────────────┐│
│  │  │ 📻 Custom Radio      │  │ 🖼️ Infinite          │  │ 🔍 Research    ││
│  │  │    Show              │  │    Wallpaper         │  │    Assistant   ││
│  │  │ ──────────────────── │  │ ──────────────────── │  │ ────────────── ││
│  │  │ 🟢 Running           │  │ 🟢 Running           │  │ ⏸️ Paused      ││
│  │  │ Last: 2 min ago      │  │ Last: 5 min ago      │  │ Last: 1 hr ago ││
│  │  │ Tasks: 47 completed  │  │ Images: 23 generated │  │ Queries: 156   ││
│  │  │ [▶][⏸][⚙️]          │  │ [▶][⏸][⚙️]          │  │ [▶][⏸][⚙️]    ││
│  │  └──────────────────────┘  └──────────────────────┘  └────────────────┘│
│  │                                                                        │
│  │  ┌──────────────────────┐  ┌──────────────────────┐  ┌────────────────┐│
│  │  │ 📧 Email Digest      │  │ 📈 Market Analyzer   │  │ + New          ││
│  │  │ ──────────────────── │  │ ──────────────────── │  │   Workflow     ││
│  │  │ ⏰ Scheduled (8am)   │  │ ⏹️ Stopped           │  │                ││
│  │  │ Next: Tomorrow       │  │ Last: 3 days ago     │  │   Drag a       ││
│  │  │ Emails: 5/week       │  │ Analyses: 890        │  │   template or  ││
│  │  │ [▶][⏸][⚙️]          │  │ [▶][⏸][⚙️]          │  │   start blank  ││
│  │  └──────────────────────┘  └──────────────────────┘  └────────────────┘│
│  └──────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│  ┌─ Recent Activity ────────────────────────────────────────────────────┐  │
│  │ 14:23 📻 Custom Radio Show generated "AI Trends" segment             │  │
│  │ 14:18 🖼️ Infinite Wallpaper created "Sunset Mountains" (4K)         │  │
│  │ 14:15 📻 Custom Radio Show processed 3 new topics from HN            │  │
│  │ 14:02 🖼️ Infinite Wallpaper uploaded to display rotation            │  │
│  │ [View All Activity →]                                                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7. Settings & Integrations

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ⚙️ Settings                                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────┐                                                     │
│  │ General            │  ┌─ LLM Providers ────────────────────────────────┐│
│  │ LLM Providers  ◀───│  │                                                ││
│  │ Voice Services     │  │  Provider         Status       Default Model   ││
│  │ Image Generation   │  │  ────────────────────────────────────────────  ││
│  │ Browser Settings   │  │  🟢 Anthropic     Connected    claude-3-opus   ││
│  │ Database           │  │  🟢 OpenAI        Connected    gpt-4-turbo     ││
│  │ Storage            │  │  🟢 Ollama        Connected    llama3.1:70b    ││
│  │ API Keys           │  │  🔴 Groq          Not configured               ││
│  │ Workers            │  │                                                ││
│  └────────────────────┘  │  [+ Add Provider]                              ││
│                          │                                                ││
│                          │  ┌─ Anthropic Configuration ─────────────────┐ ││
│                          │  │ API Key: [sk-ant-••••••••••••]  [Test]    │ ││
│                          │  │ Default Model: [claude-3-opus     ▼]      │ ││
│                          │  │ Max Tokens: [4096___]                     │ ││
│                          │  │ Rate Limit: [60] requests/minute          │ ││
│                          │  │                                           │ ││
│                          │  │ Available Models:                         │ ││
│                          │  │ ☑ claude-3-opus-20240229                 │ ││
│                          │  │ ☑ claude-3-sonnet-20240229               │ ││
│                          │  │ ☑ claude-3-5-sonnet-20241022             │ ││
│                          │  │ ☐ claude-3-haiku-20240307                │ ││
│                          │  └───────────────────────────────────────────┘ ││
│                          └────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Color Palette & Visual Design

### Color System

| Use Case | Light Mode | Dark Mode | Purpose |
|----------|------------|-----------|---------|
| Background | `#FAFAFA` | `#1A1A1A` | Canvas background |
| Surface | `#FFFFFF` | `#2D2D2D` | Node backgrounds |
| Primary | `#3B82F6` | `#60A5FA` | Interactive elements |
| Success | `#10B981` | `#34D399` | Running/success states |
| Warning | `#F59E0B` | `#FBBF24` | Pending/warning states |
| Error | `#EF4444` | `#F87171` | Error states |
| Text Primary | `#1F2937` | `#F9FAFB` | Main text |
| Text Secondary | `#6B7280` | `#9CA3AF` | Secondary text |
| Border | `#E5E7EB` | `#404040` | Node borders |
| Wire | `#94A3B8` | `#64748B` | Default connections |
| Wire Active | `#3B82F6` | `#60A5FA` | Active data flow |

### Node Type Colors

| Category | Accent Color | Icon |
|----------|-------------|------|
| Trigger | `#8B5CF6` (Purple) | ⚡ |
| LLM | `#06B6D4` (Cyan) | 🤖 |
| Voice | `#EC4899` (Pink) | 🔊 |
| Web | `#14B8A6` (Teal) | 🌐 |
| Image | `#F97316` (Orange) | 🖼️ |
| Queue | `#EAB308` (Yellow) | 📋 |
| Data | `#84CC16` (Lime) | 📊 |
| Control | `#6366F1` (Indigo) | 🔀 |
| Output | `#22C55E` (Green) | 📤 |

---

## Technology Stack

### Backend
- **Framework**: Django 5.0+ with Django REST Framework
- **Database**: PostgreSQL 15+ (supports JSON fields for flexible node configs)
- **Task Queue**: Celery with Redis broker (for long-running agent tasks)
- **WebSocket**: Django Channels (for real-time execution updates)
- **API Documentation**: drf-spectacular (OpenAPI 3.0)

### Frontend
- **Framework**: React 18+ with TypeScript
- **State Management**: Zustand (lightweight, hooks-based)
- **Styling**: Tailwind CSS 3.4+
- **Canvas**: React Flow (industry-standard for node-based editors)
- **Build Tool**: Webpack 5 with HMR
- **API Client**: TanStack Query (React Query)

### Development
- **Hot Reload**: Webpack Dev Server + Django runserver with auto-reload
- **Testing**: pytest (backend), Jest + React Testing Library (frontend), Playwright (E2E)
- **Type Safety**: TypeScript strict mode, Python type hints with mypy
- **Code Quality**: ESLint, Prettier, Black, isort

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Reverse Proxy**: Nginx (production)
- **Static Files**: Whitenoise or Nginx

---

## Project Structure

```
llm-agent-lab/
├── backend/                      # Django application
│   ├── manage.py
│   ├── config/                   # Django settings
│   │   ├── settings/
│   │   │   ├── base.py          # Common settings
│   │   │   ├── development.py   # Dev-specific
│   │   │   └── production.py    # Prod-specific
│   │   ├── urls.py
│   │   ├── asgi.py              # WebSocket support
│   │   └── wsgi.py
│   │
│   ├── apps/
│   │   ├── core/                # Shared utilities
│   │   │   ├── models.py        # Base models (TimeStamped, etc.)
│   │   │   └── permissions.py
│   │   │
│   │   ├── workflows/           # Workflow management
│   │   │   ├── models.py        # Workflow, Node, Connection
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   └── services/
│   │   │       ├── executor.py  # Workflow execution engine
│   │   │       └── validator.py # Workflow validation
│   │   │
│   │   ├── nodes/               # Node type definitions
│   │   │   ├── registry.py      # Node type registry
│   │   │   ├── base.py          # Base node class
│   │   │   ├── llm/             # LLM nodes
│   │   │   ├── voice/           # Voice nodes
│   │   │   ├── web/             # Web nodes
│   │   │   ├── image/           # Image nodes
│   │   │   └── queue/           # Queue nodes
│   │   │
│   │   ├── providers/           # External service integrations
│   │   │   ├── models.py        # Provider configs
│   │   │   ├── llm/
│   │   │   │   ├── base.py
│   │   │   │   ├── anthropic.py
│   │   │   │   ├── openai.py
│   │   │   │   └── ollama.py
│   │   │   ├── voice/
│   │   │   └── image/
│   │   │
│   │   ├── queues/              # Queue management
│   │   │   ├── models.py        # Queue, QueueItem
│   │   │   ├── strategies.py    # FIFO, RoundRobin, Broadcast
│   │   │   └── services.py
│   │   │
│   │   ├── executions/          # Execution tracking
│   │   │   ├── models.py        # Execution, NodeExecution
│   │   │   ├── consumers.py     # WebSocket consumers
│   │   │   └── tasks.py         # Celery tasks
│   │   │
│   │   └── assets/              # Voice samples, images, etc.
│   │       ├── models.py
│   │       └── storage.py
│   │
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── factories.py         # Test data factories
│   │   ├── test_api/
│   │   ├── test_services/
│   │   └── test_nodes/
│   │
│   └── requirements/
│       ├── base.txt
│       ├── development.txt
│       └── production.txt
│
├── frontend/                     # React application
│   ├── package.json
│   ├── tsconfig.json
│   ├── webpack.config.js
│   ├── tailwind.config.js
│   │
│   ├── src/
│   │   ├── index.tsx
│   │   ├── App.tsx
│   │   │
│   │   ├── components/
│   │   │   ├── canvas/          # Workflow canvas components
│   │   │   │   ├── Canvas.tsx
│   │   │   │   ├── Node.tsx
│   │   │   │   ├── Connection.tsx
│   │   │   │   └── NodeLibrary.tsx
│   │   │   │
│   │   │   ├── panels/          # Side panels
│   │   │   │   ├── NodeConfig.tsx
│   │   │   │   ├── ExecutionLog.tsx
│   │   │   │   └── QueueStatus.tsx
│   │   │   │
│   │   │   ├── dashboard/       # Dashboard components
│   │   │   │   ├── WorkflowCard.tsx
│   │   │   │   ├── ActivityFeed.tsx
│   │   │   │   └── QuickStats.tsx
│   │   │   │
│   │   │   └── ui/              # Shared UI components
│   │   │       ├── Button.tsx
│   │   │       ├── Input.tsx
│   │   │       ├── Modal.tsx
│   │   │       └── ...
│   │   │
│   │   ├── hooks/               # Custom React hooks
│   │   │   ├── useWorkflow.ts
│   │   │   ├── useExecution.ts
│   │   │   └── useWebSocket.ts
│   │   │
│   │   ├── stores/              # Zustand stores
│   │   │   ├── workflowStore.ts
│   │   │   ├── executionStore.ts
│   │   │   └── uiStore.ts
│   │   │
│   │   ├── api/                 # API client
│   │   │   ├── client.ts
│   │   │   ├── workflows.ts
│   │   │   ├── executions.ts
│   │   │   └── providers.ts
│   │   │
│   │   ├── types/               # TypeScript types
│   │   │   ├── workflow.ts
│   │   │   ├── node.ts
│   │   │   └── api.ts
│   │   │
│   │   └── styles/
│   │       └── globals.css
│   │
│   ├── public/
│   │   └── index.html
│   │
│   └── tests/
│       ├── components/
│       └── e2e/
│
├── docs/                         # Documentation
│   ├── DESIGN_DOCUMENT.md       # This file
│   ├── API_SPECIFICATION.md     # API documentation
│   ├── MIGRATION_PLAN.md        # Porting existing features
│   ├── CONTRIBUTING.md          # Development guidelines
│   └── architecture/
│       └── diagrams/
│
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
│
├── scripts/
│   ├── setup.sh                 # Initial setup
│   ├── dev.sh                   # Start dev environment
│   └── migrate.sh               # Database migrations
│
└── README.md
```

---

## API Design Principles

### RESTful Conventions

```
GET    /api/v1/workflows/           # List all workflows
POST   /api/v1/workflows/           # Create workflow
GET    /api/v1/workflows/{id}/      # Get workflow details
PUT    /api/v1/workflows/{id}/      # Update workflow
DELETE /api/v1/workflows/{id}/      # Delete workflow

POST   /api/v1/workflows/{id}/execute/    # Start execution
POST   /api/v1/workflows/{id}/pause/      # Pause execution
POST   /api/v1/workflows/{id}/resume/     # Resume execution
POST   /api/v1/workflows/{id}/stop/       # Stop execution
POST   /api/v1/workflows/{id}/duplicate/  # Clone workflow

GET    /api/v1/executions/                # List executions
GET    /api/v1/executions/{id}/           # Execution details
GET    /api/v1/executions/{id}/logs/      # Execution logs
WS     /ws/executions/{id}/               # Real-time updates
```

### API Features

1. **Consistent Response Format**
```json
{
  "data": { ... },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 45
  }
}
```

2. **Error Handling**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid node configuration",
    "details": {
      "field": "temperature",
      "error": "Must be between 0 and 2"
    }
  }
}
```

3. **Filtering & Pagination**
```
GET /api/v1/workflows/?status=running&page=2&per_page=10
```

4. **Webhook Support**
```
POST /api/v1/webhooks/              # Register webhook
POST /api/v1/workflows/{id}/trigger/{secret}/  # Trigger via webhook
```

---

## Testing Strategy

### Unit Tests (Backend)
- Model validation
- Serializer correctness
- Service logic
- Node type implementations
- Provider integrations (mocked)

### API Tests (Backend)
- Endpoint response codes
- Authentication/Authorization
- Payload validation
- Pagination behavior
- Error handling

### Component Tests (Frontend)
- React component rendering
- User interactions
- State management
- Canvas node operations

### Integration Tests
- Workflow execution end-to-end
- Queue processing
- WebSocket updates
- Provider API calls (sandbox)

### E2E Tests (Playwright)
- Create workflow via UI
- Add and connect nodes
- Execute and monitor
- Settings configuration

---

## Phase 1: Foundation (Current Focus)

1. **Project Setup**
   - Django project structure
   - React TypeScript with Webpack
   - Tailwind CSS configuration
   - Hot reload for both

2. **Core Models**
   - Workflow, Node, Connection
   - Basic CRUD API

3. **Canvas MVP**
   - Drag & drop nodes
   - Connect nodes with wires
   - Save/load positions

4. **Development Experience**
   - Auto-reload on code changes
   - Clear error messages
   - API documentation

---

## Success Metrics

- **Developer Experience**: <1s hot reload, comprehensive docs
- **UI Responsiveness**: <100ms interaction latency
- **API Performance**: <200ms response time for CRUD operations
- **Test Coverage**: >80% for backend, >70% for frontend
- **Extensibility**: New node type added in <50 lines of code

---

## Future Enhancements

- **Real-time Collaboration**: Multiple users editing same workflow
- **Workflow Templates**: Pre-built templates for common use cases
- **Marketplace**: Share and discover community workflows
- **Mobile App**: Monitor and trigger workflows on the go
- **AI-Assisted Design**: "Build me a workflow that..." natural language
- **Version Control**: Git-like branching and merging for workflows

---

*Document Version: 1.0*
*Last Updated: 2024-01-15*

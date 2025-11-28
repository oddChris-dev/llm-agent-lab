# Migration Plan: Flask to Django + React

This document outlines the strategy for migrating the existing LLM Agent Lab from Flask/MySQL to Django/PostgreSQL with a React TypeScript frontend.

## Migration Philosophy

1. **Incremental Migration**: New features built in new stack, existing features migrated incrementally
2. **Feature Parity First**: Ensure all existing functionality works before adding new features
3. **Data Preservation**: All existing data (agents, voices, sessions, transcripts) must be preserved
4. **No Downtime**: Support running both systems during transition

---

## Current System Inventory

### Existing Features to Migrate

| Feature | Current Implementation | New Architecture |
|---------|----------------------|------------------|
| **Text Generation** | HuggingFace + Local Llama | Node: `llm.local`, Provider: Ollama |
| **Voice Synthesis (TTS)** | XTTS-v2 local | Node: `voice.tts`, Provider: XTTS |
| **Speech Recognition** | Vosk local | Node: `voice.stt`, Provider: Vosk |
| **Browser Automation** | Selenium + mitmproxy | Node: `web.browser_watch` |
| **Web Search** | Google scraping | Node: `web.search` |
| **Page Fetching** | Selenium + BeautifulSoup | Node: `web.fetch` |
| **Media Playback** | VLC | Service: MediaPlayer (background) |
| **Agent Prompts** | Agents table | Node configs + templates |
| **Game Sessions** | Sessions/Games tables | Workflows + Executions |
| **Voice Samples** | Voices table (BLOB) | Assets table (file storage) |
| **Transcripts** | Transcripts table | Execution logs + outputs |
| **History** | SessionHistory table | Execution logs |

### Existing Code Mapping

```
EXISTING                          NEW ARCHITECTURE
────────────────────────────────────────────────────────────────────
systems/text_generator.py    →    backend/apps/providers/llm/local.py
systems/text_to_speach.py    →    backend/apps/providers/voice/xtts.py
systems/speach_listener.py   →    backend/apps/providers/voice/vosk.py
systems/browser.py           →    backend/apps/nodes/web/browser.py
systems/browser_proxy.py     →    backend/apps/nodes/web/proxy.py
systems/game_system.py       →    backend/apps/workflows/services/executor.py
systems/game_moves.py        →    backend/apps/workflows/services/executor.py
systems/media_player.py      →    backend/apps/services/media.py
systems/transcript_player.py →    backend/apps/services/transcript.py
systems/app.py               →    Django settings + Celery
systems/database.py          →    Django ORM
systems/config.py            →    Django settings + environment

models/*.py                  →    backend/apps/*/models.py
pages/*.py                   →    backend/apps/*/views.py + serializers.py
utils/*.py                   →    backend/apps/core/utils/

static/                      →    frontend/src/styles/
templates/                   →    frontend/src/components/
```

---

## Feature Encapsulation: Node Types

Each existing feature becomes one or more node types in the new system:

### 1. LLM Nodes

#### `llm.local` (Existing Local Model)
```python
# Wraps existing TextGenerator
class LocalLLMNode(BaseNode):
    type = "llm.local"
    name = "Local LLM (Ollama)"
    category = "llm"

    inputs = [
        Port("prompt", "string", required=True),
        Port("context", "string"),
        Port("system_prompt", "string"),
    ]

    outputs = [
        Port("response", "string"),
        Port("usage", "object"),
    ]

    config_schema = {
        "model": {"type": "string", "default": "llama3.1:8b"},
        "temperature": {"type": "number", "default": 0.7},
        "max_tokens": {"type": "integer", "default": 512},
    }

    async def execute(self, inputs, config, context):
        provider = OllamaProvider(config.get("base_url", "http://localhost:11434"))
        response = await provider.generate(
            model=config["model"],
            prompt=inputs["prompt"],
            system=inputs.get("system_prompt") or config.get("system_prompt"),
            context=inputs.get("context"),
            temperature=config["temperature"],
            max_tokens=config["max_tokens"],
        )
        return {"response": response.text, "usage": response.usage}
```

#### `llm.claude` (New Provider)
```python
class ClaudeNode(BaseNode):
    type = "llm.claude"
    name = "Claude (Anthropic)"
    category = "llm"

    # Similar structure, uses Anthropic API
```

#### `llm.openai` (New Provider)
```python
class OpenAINode(BaseNode):
    type = "llm.openai"
    name = "GPT (OpenAI)"
    category = "llm"

    # Similar structure, uses OpenAI API
```

### 2. Voice Nodes

#### `voice.tts` (Existing XTTS-v2)
```python
class TTSNode(BaseNode):
    type = "voice.tts"
    name = "Text to Speech"
    category = "voice"

    inputs = [
        Port("text", "string", required=True),
        Port("voice_id", "string"),  # Reference to voice asset
    ]

    outputs = [
        Port("audio", "audio"),
        Port("duration", "number"),
    ]

    config_schema = {
        "provider": {"type": "string", "enum": ["xtts", "elevenlabs", "openai"]},
        "voice_id": {"type": "string"},
        "speed": {"type": "number", "default": 1.0},
    }

    async def execute(self, inputs, config, context):
        # Maps to existing TextToSpeach class functionality
        voice_asset = await Asset.objects.aget(id=inputs.get("voice_id") or config["voice_id"])
        provider = XTTSProvider()

        audio_data = await provider.synthesize(
            text=inputs["text"],
            voice_sample_path=voice_asset.file_path,
        )

        # Store result as temporary asset
        output_asset = await save_temp_audio(audio_data)

        return {
            "audio": output_asset.url,
            "duration": audio_data.duration_seconds,
        }
```

#### `voice.stt` (Existing Vosk)
```python
class STTNode(BaseNode):
    type = "voice.stt"
    name = "Speech to Text"
    category = "voice"

    inputs = [
        Port("audio", "audio", required=True),
    ]

    outputs = [
        Port("text", "string"),
        Port("confidence", "number"),
    ]

    # Wraps existing SpeachListener functionality
```

#### `voice.play` (Audio Playback)
```python
class PlayAudioNode(BaseNode):
    type = "voice.play"
    name = "Play Audio"
    category = "voice"

    inputs = [
        Port("audio", "audio", required=True),
    ]

    outputs = [
        Port("completed", "boolean"),
    ]

    # Wraps MediaPlayer for audio output
```

### 3. Web Nodes

#### `web.browser_watch` (Existing Browser Watcher)
```python
class BrowserWatchNode(BaseNode):
    type = "web.browser_watch"
    name = "Browser Watcher"
    category = "web"

    inputs = []  # Trigger node - no inputs

    outputs = [
        Port("url", "string"),
        Port("title", "string"),
        Port("content", "string"),
    ]

    config_schema = {
        "url_patterns": {"type": "array", "items": {"type": "string"}},
        "exclude_patterns": {"type": "array"},
        "poll_interval_seconds": {"type": "integer", "default": 5},
    }

    async def execute(self, inputs, config, context):
        # Uses browser proxy to detect URL changes
        # Streams events when URLs match patterns
        pass
```

#### `web.search` (Existing Web Search)
```python
class WebSearchNode(BaseNode):
    type = "web.search"
    name = "Web Search"
    category = "web"

    inputs = [
        Port("query", "string", required=True),
    ]

    outputs = [
        Port("results", "array"),
    ]

    config_schema = {
        "provider": {"type": "string", "enum": ["google", "bing", "duckduckgo"]},
        "max_results": {"type": "integer", "default": 10},
    }

    async def execute(self, inputs, config, context):
        # Wraps existing BrowserSystem.search()
        browser = BrowserService()
        results = await browser.search(inputs["query"], max_results=config["max_results"])
        return {"results": results}
```

#### `web.fetch` (Existing Page Fetch)
```python
class WebFetchNode(BaseNode):
    type = "web.fetch"
    name = "Fetch Web Page"
    category = "web"

    inputs = [
        Port("url", "string", required=True),
    ]

    outputs = [
        Port("content", "string"),
        Port("title", "string"),
        Port("links", "array"),
    ]

    config_schema = {
        "timeout_seconds": {"type": "integer", "default": 30},
        "extract_links": {"type": "boolean", "default": True},
        "clean_html": {"type": "boolean", "default": True},
    }
```

### 4. Image Nodes (New)

#### `image.generate` (Stable Diffusion)
```python
class ImageGenerateNode(BaseNode):
    type = "image.generate"
    name = "Generate Image"
    category = "image"

    inputs = [
        Port("prompt", "string", required=True),
        Port("negative_prompt", "string"),
    ]

    outputs = [
        Port("image", "image"),
    ]

    config_schema = {
        "provider": {"type": "string", "enum": ["comfyui", "automatic1111", "dalle"]},
        "model": {"type": "string"},
        "width": {"type": "integer", "default": 1024},
        "height": {"type": "integer", "default": 1024},
        "steps": {"type": "integer", "default": 30},
    }
```

#### `image.comfyui` (ComfyUI Workflow)
```python
class ComfyUINode(BaseNode):
    type = "image.comfyui"
    name = "ComfyUI Workflow"
    category = "image"

    inputs = [
        Port("workflow_json", "object"),
        Port("inputs", "object"),
    ]

    outputs = [
        Port("images", "array"),
    ]

    config_schema = {
        "server_url": {"type": "string", "default": "http://localhost:8188"},
        "workflow_file": {"type": "string"},  # Path to workflow JSON
    }
```

### 5. Queue Nodes

#### `queue.fifo`
```python
class FIFOQueueNode(BaseNode):
    type = "queue.fifo"
    name = "FIFO Queue"
    category = "queue"

    inputs = [
        Port("input", "any", required=True),
    ]

    outputs = [
        Port("output", "any"),
    ]

    config_schema = {
        "queue_id": {"type": "string"},  # Link to persistent queue
        "max_size": {"type": "integer", "default": 1000},
    }

    async def execute(self, inputs, config, context):
        queue = await Queue.objects.aget(id=config["queue_id"])
        await queue.enqueue(inputs["input"])

        # Dequeue happens asynchronously based on downstream demand
```

#### `queue.round_robin`
```python
class RoundRobinNode(BaseNode):
    type = "queue.round_robin"
    name = "Round Robin"
    category = "queue"

    # Distributes inputs across multiple outputs
```

#### `queue.broadcast`
```python
class BroadcastNode(BaseNode):
    type = "queue.broadcast"
    name = "Broadcast"
    category = "queue"

    # Sends input to ALL connected outputs
```

### 6. Control Nodes

#### `control.condition`
```python
class ConditionNode(BaseNode):
    type = "control.condition"
    name = "Condition"
    category = "control"

    inputs = [
        Port("value", "any", required=True),
    ]

    outputs = [
        Port("if_true", "any"),
        Port("if_false", "any"),
    ]

    config_schema = {
        "expression": {"type": "string"},  # e.g., "{{value.length > 100}}"
    }
```

#### `control.loop`
```python
class LoopNode(BaseNode):
    type = "control.loop"
    name = "Loop"
    category = "control"

    inputs = [
        Port("items", "array", required=True),
    ]

    outputs = [
        Port("item", "any"),
        Port("index", "number"),
        Port("completed", "boolean"),
    ]
```

---

## Data Migration

### Phase 1: Schema Migration

```sql
-- Create new PostgreSQL schema (see DATABASE_SCHEMA.md)
-- This is handled by Django migrations

-- Export from MySQL
mysqldump -u user -p llm_agent_lab > mysql_backup.sql
```

### Phase 2: Data Transfer Scripts

#### Migrate Agents to Node Templates
```python
# backend/management/commands/migrate_agents.py

from django.core.management.base import BaseCommand
from apps.workflows.models import Workflow, Node
from legacy.models import Agent  # Legacy MySQL model

class Command(BaseCommand):
    def handle(self, *args, **options):
        for agent in Agent.objects.all():
            # Create a workflow template for each agent
            workflow = Workflow.objects.create(
                name=f"Agent: {agent.name}",
                description=f"Migrated from legacy agent: {agent.name}",
                is_template=True,
                settings={
                    "legacy_agent_name": agent.name,
                    "legacy_role": agent.role,
                }
            )

            # Create LLM node with agent's prompt
            Node.objects.create(
                workflow=workflow,
                type="llm.local",
                name=agent.name,
                position_x=200,
                position_y=200,
                config={
                    "system_prompt": agent.prompt,
                    "voice": agent.voice,  # Will link to voice asset
                }
            )

            self.stdout.write(f"Migrated agent: {agent.name}")
```

#### Migrate Voices to Assets
```python
# backend/management/commands/migrate_voices.py

from django.core.management.base import BaseCommand
from apps.assets.models import Asset
from legacy.models import Voice
import os

class Command(BaseCommand):
    def handle(self, *args, **options):
        for voice in Voice.objects.all():
            # Save binary data to file
            file_path = f"assets/voices/{voice.name}.wav"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'wb') as f:
                f.write(voice.data)

            # Create asset record
            Asset.objects.create(
                name=voice.name,
                type='voice_sample',
                file_path=file_path,
                file_size=len(voice.data),
                mime_type='audio/wav',
                metadata={
                    "legacy_voice_name": voice.name,
                }
            )

            self.stdout.write(f"Migrated voice: {voice.name}")
```

#### Migrate Games to Workflow Templates
```python
# backend/management/commands/migrate_games.py

class Command(BaseCommand):
    def handle(self, *args, **options):
        for game in Game.objects.all():
            # Parse game rules to determine node structure
            workflow = Workflow.objects.create(
                name=game.name,
                description=game.rules,
                is_template=True,
                settings={
                    "legacy_game_name": game.name,
                    "variables": dict(game.variables.all().values_list('name', 'value')),
                }
            )

            # Create nodes based on game players (agents in turn order)
            # This requires analyzing session_players to understand the flow
```

#### Migrate Sessions to Executions
```python
# backend/management/commands/migrate_sessions.py

class Command(BaseCommand):
    def handle(self, *args, **options):
        for session in Session.objects.all():
            # Find or create corresponding workflow
            workflow = Workflow.objects.get(
                settings__legacy_game_name=session.game
            )

            # Create execution record
            execution = Execution.objects.create(
                workflow=workflow,
                status='completed',  # Legacy sessions are historical
                context={
                    "legacy_session_id": session.id,
                    "settings": dict(session.settings.all().values_list('name', 'value')),
                },
                trigger_type='legacy_migration',
            )

            # Migrate history to execution logs
            for history in session.history.all():
                ExecutionLog.objects.create(
                    execution=execution,
                    level='info',
                    message=history.content,
                    data={
                        "role": history.role,
                        "timestamp": history.timestamp.isoformat(),
                    },
                    timestamp=history.timestamp,
                )

            # Migrate transcripts to node outputs
            for transcript in session.transcripts.all():
                # Store as execution artifact
                pass
```

### Phase 3: Verification

```python
# backend/management/commands/verify_migration.py

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Count comparisons
        assert Workflow.objects.filter(is_template=True).count() >= Game.objects.count()
        assert Asset.objects.filter(type='voice_sample').count() == Voice.objects.count()

        # Verify data integrity
        for voice in Voice.objects.all():
            asset = Asset.objects.get(metadata__legacy_voice_name=voice.name)
            assert os.path.exists(asset.file_path)
            with open(asset.file_path, 'rb') as f:
                assert len(f.read()) == len(voice.data)

        self.stdout.write("Migration verification passed!")
```

---

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- [x] Design documents (this phase)
- [ ] Django project setup with apps structure
- [ ] React TypeScript setup with Webpack
- [ ] Basic CRUD API for Workflows/Nodes/Connections
- [ ] Canvas MVP (React Flow integration)
- [ ] Database migrations
- [ ] Development environment with hot reload

### Phase 2: Core Migration (Weeks 3-4)
- [ ] Provider abstraction layer
- [ ] Migrate TextGenerator → Ollama provider
- [ ] Migrate TTS → XTTS provider
- [ ] Migrate STT → Vosk provider
- [ ] Node type registry
- [ ] Basic execution engine

### Phase 3: Web Features (Weeks 5-6)
- [ ] Migrate BrowserSystem → web nodes
- [ ] Browser proxy integration
- [ ] Web search node
- [ ] Page fetch node
- [ ] URL pattern matching

### Phase 4: Queues & Control Flow (Weeks 7-8)
- [ ] Queue models and API
- [ ] FIFO queue node
- [ ] Round robin node
- [ ] Broadcast node
- [ ] Conditional routing

### Phase 5: New Providers (Weeks 9-10)
- [ ] Claude (Anthropic) integration
- [ ] OpenAI integration
- [ ] ElevenLabs TTS (optional)
- [ ] ComfyUI integration

### Phase 6: Data Migration (Week 11)
- [ ] Migration scripts
- [ ] Data verification
- [ ] Legacy system bridge (dual-write period)

### Phase 7: Testing & Polish (Week 12)
- [ ] Unit tests (80% coverage)
- [ ] API integration tests
- [ ] E2E tests with Playwright
- [ ] Performance optimization
- [ ] Documentation finalization

---

## Risk Mitigation

### Risk: Data Loss During Migration
**Mitigation**:
- Full MySQL backup before migration
- Dual-write period where both systems receive updates
- Rollback scripts prepared

### Risk: Performance Regression
**Mitigation**:
- Benchmark existing system before migration
- Load test new system with equivalent workloads
- Async processing for long-running tasks

### Risk: Feature Gaps
**Mitigation**:
- Detailed feature inventory (this document)
- Manual testing checklist for each feature
- User acceptance testing before full cutover

### Risk: GPU Resource Contention
**Mitigation**:
- Preserve existing CUDA lock pattern
- Celery task queue for GPU operations
- Configurable concurrency limits

---

## Backwards Compatibility

During transition, the system supports:

1. **Legacy API Bridge**: Routes old Flask endpoints to new Django views
2. **Database Views**: Legacy MySQL views that read from PostgreSQL
3. **Config Compatibility**: Reads existing `config.json` format

```python
# backend/legacy_bridge/middleware.py

class LegacyAPIBridge:
    """
    Routes /old-api/* to new API endpoints with translation.
    """

    ROUTE_MAP = {
        '/agents': '/api/v1/workflows/?is_template=true',
        '/voices': '/api/v1/assets/?type=voice_sample',
        '/sessions': '/api/v1/executions/',
    }

    def translate_request(self, request):
        # Convert old request format to new
        pass

    def translate_response(self, response):
        # Convert new response format to old
        pass
```

---

## Success Criteria

Migration is complete when:

1. **All existing features work** in new system
2. **All data migrated** and verified
3. **No regressions** in performance
4. **Tests passing** at required coverage
5. **Documentation complete** for all APIs
6. **Users can create** custom radio show workflow entirely in UI
7. **Users can create** infinite wallpaper workflow entirely in UI

---

*Migration Plan Version: 1.0*
*Last Updated: 2024-01-15*

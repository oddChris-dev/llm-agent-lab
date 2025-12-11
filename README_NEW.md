# LLM Agent Lab

A visual workflow orchestration platform for AI agents. Design, build, and execute complex multi-agent workflows through an intuitive drag-and-drop interface.

## Features

- **Visual Workflow Builder**: Drag-and-drop nodes, connect with wires
- **Multiple LLM Providers**: Claude, GPT, Ollama (local)
- **Voice Integration**: Text-to-speech and speech-to-text
- **Web Automation**: Browser watching, web search, page scraping
- **Image Generation**: Stable Diffusion via ComfyUI
- **Flexible Queues**: FIFO, round-robin, broadcast distribution
- **Real-time Monitoring**: WebSocket-based execution tracking
- **API-Driven**: Full REST API for automation

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 15+ (or use SQLite for development)
- Redis (optional, for production)

### Setup (Linux/macOS)

```bash
# Clone the repository
git clone https://github.com/yourusername/llm-agent-lab.git
cd llm-agent-lab

# Run setup script
./scripts/setup.sh

# Start development servers
./scripts/dev.sh
```

### Setup (Windows)

**Option 1: PowerShell (Recommended for native Windows)**

```powershell
# Clone the repository
git clone https://github.com/yourusername/llm-agent-lab.git
cd llm-agent-lab

# If you get execution policy errors, run this first:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run setup script
.\scripts\setup.ps1

# Start development servers
.\scripts\dev.ps1
```

**Option 2: WSL2 (Windows Subsystem for Linux)**

If you prefer a Linux environment on Windows:

```bash
# Install WSL2 from PowerShell (admin):
wsl --install

# Open WSL and clone the repo
wsl
cd /mnt/c/path/to/your/projects
git clone https://github.com/yourusername/llm-agent-lab.git
cd llm-agent-lab

# Use Linux scripts
./scripts/setup.sh
./scripts/dev.sh
```

**Option 3: Docker Desktop (Most Consistent)**

```powershell
# Install Docker Desktop for Windows
# Then run:
cd docker
docker-compose up
```

### Development URLs

Once running, these services are available:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/v1/
- API Docs: http://localhost:8000/api/docs/
- Admin: http://localhost:8000/admin/ (admin/admin)

### Using Docker

```bash
cd docker
docker-compose up
```

## Project Structure

```
llm-agent-lab/
├── backend/              # Django REST API
│   ├── apps/
│   │   ├── workflows/    # Workflow management
│   │   ├── nodes/        # Node type registry
│   │   ├── providers/    # LLM, voice, image providers
│   │   ├── queues/       # Queue management
│   │   ├── executions/   # Execution tracking
│   │   └── assets/       # File storage
│   └── config/           # Django settings
│
├── frontend/             # React TypeScript app
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── hooks/        # Custom hooks
│   │   ├── api/          # API client
│   │   └── stores/       # State management
│   └── tests/            # Jest & Playwright tests
│
├── docs/                 # Documentation
│   ├── DESIGN_DOCUMENT.md
│   ├── DATABASE_SCHEMA.md
│   ├── API_SPECIFICATION.md
│   └── MIGRATION_PLAN.md
│
├── docker/               # Docker configuration
└── scripts/              # Development scripts
```

## Documentation

- [Design Document](docs/DESIGN_DOCUMENT.md) - Architecture and UX design
- [Database Schema](docs/DATABASE_SCHEMA.md) - PostgreSQL schema
- [API Specification](docs/API_SPECIFICATION.md) - REST API documentation
- [Migration Plan](docs/MIGRATION_PLAN.md) - Porting existing features

## Development

### Backend

**Linux/macOS:**
```bash
cd backend
source venv/bin/activate

# Run tests
pytest

# Run with coverage
pytest --cov=apps

# Format code
black .
isort .

# Type checking
mypy apps
```

**Windows (PowerShell):**
```powershell
cd backend
.\venv\Scripts\Activate.ps1

# Run tests
pytest

# Run with coverage
pytest --cov=apps

# Format code
black .
isort .

# Type checking
mypy apps
```

### Frontend

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm run test:coverage

# E2E tests
npm run test:e2e

# Lint
npm run lint

# Type check
npm run type-check

# Clean build artifacts (works on all platforms)
npm run clean
```

### Environment Configuration

Copy the example environment file and customize it:

**Linux/macOS:**
```bash
cp backend/.env.example backend/.env
```

**Windows:**
```powershell
copy backend\.env.example backend\.env
```

See `backend/.env.example` for all available configuration options.

## API Examples

### Create a Workflow

```bash
curl -X POST http://localhost:8000/api/v1/workflows/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Workflow",
    "description": "A simple workflow"
  }'
```

### Add a Node

```bash
curl -X POST http://localhost:8000/api/v1/workflows/{id}/nodes/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "llm.claude",
    "name": "Analyzer",
    "position": {"x": 100, "y": 100},
    "config": {
      "model": "claude-3-opus-20240229",
      "temperature": 0.7
    }
  }'
```

### Execute Workflow

```bash
curl -X POST http://localhost:8000/api/v1/workflows/{id}/execute/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "trigger_data": {
      "input": "Analyze this topic"
    }
  }'
```

## Use Cases

### Custom Radio Show Generator
Watch your web browsing, extract topics, generate scripts, and produce voice content.

### Infinite Wallpaper
Generate continuous artistic wallpapers using Stable Diffusion with prompt chains.

### Research Assistant
Multi-agent workflow for web research, summarization, and report generation.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

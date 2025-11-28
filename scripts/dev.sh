#!/bin/bash

# Development script - starts both backend and frontend with hot reload
# Usage: ./scripts/dev.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting LLM Agent Lab Development Environment${NC}"
echo "================================================"

# Check if required tools are installed
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}Python 3 is required but not installed.${NC}" >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo -e "${RED}Node.js is required but not installed.${NC}" >&2; exit 1; }

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down...${NC}"
    kill $(jobs -p) 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start PostgreSQL if using Docker (optional)
if command -v docker >/dev/null 2>&1; then
    echo -e "${YELLOW}Checking PostgreSQL...${NC}"
    if ! docker ps | grep -q agent-lab-postgres; then
        echo "Starting PostgreSQL container..."
        docker run -d \
            --name agent-lab-postgres \
            -e POSTGRES_DB=agent_lab \
            -e POSTGRES_USER=postgres \
            -e POSTGRES_PASSWORD=postgres \
            -p 5432:5432 \
            postgres:15-alpine 2>/dev/null || true
        sleep 3
    fi
fi

# Backend setup
echo -e "${YELLOW}Setting up backend...${NC}"
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -q -r requirements/development.txt

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@localhost', 'admin')
    print('Created superuser: admin/admin')
" 2>/dev/null || true

# Start Django development server
echo -e "${GREEN}Starting Django server on http://localhost:8000${NC}"
python manage.py runserver 0.0.0.0:8000 &
DJANGO_PID=$!

cd ..

# Frontend setup
echo -e "${YELLOW}Setting up frontend...${NC}"
cd frontend

# Install npm dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing npm packages..."
    npm install
fi

# Start webpack dev server
echo -e "${GREEN}Starting Webpack Dev Server on http://localhost:3000${NC}"
npm run dev &
WEBPACK_PID=$!

cd ..

echo ""
echo -e "${GREEN}Development environment is ready!${NC}"
echo "================================================"
echo -e "Frontend: ${GREEN}http://localhost:3000${NC}"
echo -e "Backend API: ${GREEN}http://localhost:8000/api/v1/${NC}"
echo -e "API Docs: ${GREEN}http://localhost:8000/api/docs/${NC}"
echo -e "Admin: ${GREEN}http://localhost:8000/admin/${NC} (admin/admin)"
echo "================================================"
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for both processes
wait $DJANGO_PID $WEBPACK_PID

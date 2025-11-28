#!/bin/bash

# Initial setup script for LLM Agent Lab
# Usage: ./scripts/setup.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}LLM Agent Lab - Initial Setup${NC}"
echo "================================"

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3.10+${NC}"
    exit 1
fi
echo "  Python: $(python3 --version)"

# Node
if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js is not installed. Please install Node.js 18+${NC}"
    exit 1
fi
echo "  Node.js: $(node --version)"

# npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}npm is not installed.${NC}"
    exit 1
fi
echo "  npm: $(npm --version)"

# Docker (optional)
if command -v docker &> /dev/null; then
    echo "  Docker: $(docker --version | cut -d' ' -f3 | tr -d ',')"
else
    echo -e "  ${YELLOW}Docker: Not installed (optional)${NC}"
fi

echo ""
echo -e "${YELLOW}Setting up backend...${NC}"
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate and install dependencies
source venv/bin/activate
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements/development.txt

# Create .env file
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOF
DJANGO_SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DEBUG=True
USE_SQLITE=true
CELERY_EAGER=true
EOF
fi

# Create directories
mkdir -p static media staticfiles

cd ..

echo ""
echo -e "${YELLOW}Setting up frontend...${NC}"
cd frontend

# Install npm dependencies
echo "Installing npm dependencies..."
npm install

cd ..

echo ""
echo -e "${YELLOW}Creating documentation directory...${NC}"
mkdir -p docs

echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo "================================"
echo ""
echo "Next steps:"
echo "  1. Review backend/.env and update settings as needed"
echo "  2. Run './scripts/dev.sh' to start the development servers"
echo "  3. Open http://localhost:3000 in your browser"
echo ""
echo "For production setup, see docs/DEPLOYMENT.md"

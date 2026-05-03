#!/bin/bash

# Valura AI System - Start Script
# This script starts the backend API server with integrated UI

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   🚀 Valura AI System Startup         ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found!${NC}"
    echo -e "${YELLOW}Please create a .env file with your OPENAI_API_KEY${NC}"
    echo -e "${YELLOW}You can copy .env.example to .env and add your API key${NC}"
    exit 1
fi

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Error: Python is not installed!${NC}"
    exit 1
fi

# Check if required packages are installed
echo -e "${BLUE}📦 Checking dependencies...${NC}"
if ! python -c "import fastapi" &> /dev/null; then
    echo -e "${YELLOW}⚠️  Dependencies not installed. Installing...${NC}"
    pip install -r requirements.txt
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Create PID directory
mkdir -p .pids

# Kill any existing processes on port 9000
echo -e "${BLUE}🧹 Cleaning up existing processes...${NC}"
lsof -ti:9000 | xargs kill -9 2>/dev/null || true

# Start Backend API Server with integrated UI (Port 9000)
echo -e "${GREEN}🔧 Starting Valura AI Server on port 9000...${NC}"
nohup python -m uvicorn src.api.app:app --host 0.0.0.0 --port 9000 --reload > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > .pids/backend.pid
echo -e "${GREEN}✅ Server started (PID: $BACKEND_PID)${NC}"

# Wait a moment for server to start
sleep 3

# Check if server is running
if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}✅ Server is running${NC}"
else
    echo -e "${RED}❌ Server failed to start. Check logs/backend.log${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   ✨ System Started Successfully!      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📍 UI Dashboard:${NC} http://localhost:9000"
echo -e "${GREEN}📍 API Endpoint:${NC} http://localhost:9000/query"
echo -e "${GREEN}📍 API Docs:${NC} http://localhost:9000/docs"
echo -e "${GREEN}📍 Prometheus Metrics:${NC} http://localhost:9000/metrics"
echo ""
echo -e "${YELLOW}📝 Logs:${NC}"
echo -e "   Server: logs/backend.log"
echo ""
echo -e "${YELLOW}🛑 To stop the system, run:${NC} ./stop.sh"
echo ""

# Optional: Open browser (uncomment if desired)
# sleep 1
# if command -v xdg-open &> /dev/null; then
#     xdg-open http://localhost:9000
# elif command -v open &> /dev/null; then
#     open http://localhost:9000
# fi

#!/bin/bash

# Valura AI System - Stop Script
# This script stops the Valura AI server

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   🛑 Valura AI System Shutdown        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Function to stop a process
stop_process() {
    local name=$1
    local pid_file=$2
    local port=$3
    
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${YELLOW}🛑 Stopping $name (PID: $PID)...${NC}"
            kill $PID 2>/dev/null || true
            sleep 1
            
            # Force kill if still running
            if ps -p $PID > /dev/null 2>&1; then
                echo -e "${YELLOW}⚠️  Force stopping $name...${NC}"
                kill -9 $PID 2>/dev/null || true
            fi
            
            echo -e "${GREEN}✅ $name stopped${NC}"
        else
            echo -e "${YELLOW}⚠️  $name was not running (PID: $PID)${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}⚠️  No PID file found for $name${NC}"
    fi
    
    # Also kill any process on the port
    if [ ! -z "$port" ]; then
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
    fi
}

# Stop Valura AI Server
stop_process "Valura AI Server" ".pids/backend.pid" "9000"

# Clean up PID directory
if [ -d ".pids" ]; then
    rmdir .pids 2>/dev/null || true
fi

echo ""
echo -e "${GREEN}✅ Server stopped successfully!${NC}"
echo ""
echo -e "${YELLOW}📝 Logs are preserved in:${NC}"
echo -e "   logs/backend.log"
echo ""
echo -e "${BLUE}🚀 To start the system again, run:${NC} ./start.sh"
echo ""

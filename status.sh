#!/bin/bash

# Valura AI System - Status Script
# This script checks the status of the Valura AI server

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   📊 Valura AI System Status          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Function to check process status
check_process() {
    local name=$1
    local pid_file=$2
    local port=$3
    local url=$4
    
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $name is running${NC}"
            echo -e "   PID: $PID"
            echo -e "   Port: $port"
            echo -e "   URL: $url"
            
            # Check if port is actually listening
            if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
                echo -e "   ${GREEN}Port $port is listening${NC}"
            else
                echo -e "   ${YELLOW}⚠️  Port $port is not listening${NC}"
            fi
            return 0
        else
            echo -e "${RED}❌ $name is not running${NC}"
            echo -e "   ${YELLOW}PID file exists but process is dead (PID: $PID)${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ $name is not running${NC}"
        echo -e "   ${YELLOW}No PID file found${NC}"
        
        # Check if something else is on the port
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            PORT_PID=$(lsof -ti:$port)
            echo -e "   ${YELLOW}⚠️  Port $port is in use by PID: $PORT_PID${NC}"
        fi
        return 1
    fi
}

# Check Valura AI Server
check_process "Valura AI Server" ".pids/backend.pid" "9000" "http://localhost:9000"
SERVER_STATUS=$?
echo ""

# Overall status
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
if [ $SERVER_STATUS -eq 0 ]; then
    echo -e "${GREEN}✅ System is operational!${NC}"
    echo ""
    echo -e "${GREEN}📍 Access Points:${NC}"
    echo -e "   UI Dashboard: http://localhost:9000"
    echo -e "   Backend API: http://localhost:9000/query"
    echo -e "   API Docs: http://localhost:9000/docs"
    echo -e "   Prometheus Metrics: http://localhost:9000/metrics"
else
    echo -e "${RED}❌ System is not running${NC}"
    echo -e "${YELLOW}   Run ./start.sh to start the system${NC}"
fi
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Show recent logs if server is running
if [ $SERVER_STATUS -eq 0 ]; then
    echo -e "${YELLOW}📝 Recent Logs:${NC}"
    if [ -f "logs/backend.log" ]; then
        echo -e "${BLUE}Server (last 5 lines):${NC}"
        tail -n 5 logs/backend.log | sed 's/^/   /'
        echo ""
    fi
fi

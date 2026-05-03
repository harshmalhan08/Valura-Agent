#!/bin/bash

# Install Prometheus Client Package
# This script installs the prometheus-client package in the Valura virtual environment

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Installing Prometheus Client         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "Valura" ]; then
    echo -e "${RED}❌ Error: Virtual environment 'Valura' not found!${NC}"
    echo -e "${YELLOW}Please create it first: python -m venv Valura${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${BLUE}📦 Activating virtual environment...${NC}"
source Valura/bin/activate

# Install prometheus-client
echo -e "${BLUE}📦 Installing prometheus-client...${NC}"
pip install prometheus-client>=0.20.0

# Verify installation
echo ""
echo -e "${BLUE}🔍 Verifying installation...${NC}"
if python -c "import prometheus_client" 2>/dev/null; then
    echo -e "${GREEN}✅ prometheus-client installed successfully!${NC}"
else
    echo -e "${RED}❌ Installation verification failed!${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}✅ Installation complete!${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}You can now start the server with:${NC} ./start.sh"
echo ""

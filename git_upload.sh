#!/bin/bash

# Git Upload Script for Linux/Mac
# This script helps you upload your code to GitHub

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Git Upload Helper                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Error: Git is not installed!${NC}"
    echo -e "${YELLOW}Please install Git from: https://git-scm.com${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Git is installed${NC}"
echo ""

# Check if already initialized
if [ -d ".git" ]; then
    echo -e "${BLUE}ℹ️  Git repository already initialized${NC}"
else
    echo -e "${BLUE}📦 Initializing Git repository...${NC}"
    git init
    echo -e "${GREEN}✅ Git repository initialized${NC}"
fi
echo ""

# Show current status
echo -e "${BLUE}📊 Current Git status:${NC}"
git status
echo ""

# Prompt for GitHub repository URL
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║ Please provide your GitHub repository URL${NC}"
echo -e "${BLUE}║ Example: https://github.com/username/repo-name.git${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
read -p "Enter repository URL: " REPO_URL

if [ -z "$REPO_URL" ]; then
    echo -e "${RED}❌ Error: Repository URL cannot be empty!${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}📦 Adding files to Git...${NC}"
git add .

echo -e "${BLUE}💾 Creating commit...${NC}"
git commit -m "Initial commit: Valura AI Agent Ecosystem with Prometheus monitoring"

echo -e "${BLUE}🔗 Adding remote repository...${NC}"
git remote remove origin 2>/dev/null
git remote add origin "$REPO_URL"

echo -e "${BLUE}🚀 Pushing to GitHub...${NC}"
git branch -M main
git push -u origin main

echo ""
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}✅ Code uploaded to GitHub!${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Your repository:${NC} $REPO_URL"
echo ""

#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting AI Dataset Generator Toolchain...${NC}"

# 1. Check dependencies
echo -e "\n${BLUE}[1/4] Checking environment...${NC}"
if ! command -v go &> /dev/null; then
    echo -e "${RED}❌ Go is not installed. Please install Go.${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 is not installed.${NC}"
    exit 1
fi

if ! command -v poetry &> /dev/null; then
    echo -e "${YELLOW}⚠️  Poetry not found. Attempting to install dependencies with pip...${NC}"
    USE_PIP=true
else
    USE_PIP=false
fi

# 2. Compile Web Crawler (Go)
echo -e "\n${BLUE}[2/4] Compiling Web Crawler (Go)...${NC}"

# Check if webcrawler-source directory exists
if [ -d "webcrawler-source" ] && [ -f "webcrawler-source/main.go" ]; then
    cd webcrawler-source
    
    # Compile the Go project
    go build -o webcrawler .
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Go build successful: ./webcrawler-source/webcrawler${NC}"
        cd ..
    else
        echo -e "${RED}❌ Go build failed.${NC}"
        cd ..
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  webcrawler-source directory or main.go not found${NC}"
    echo -e "${YELLOW}   Continuing without compiling the webcrawler...${NC}"
fi

# 3. Install Python dependencies
echo -e "\n${BLUE}[3/4] Setting up Python...${NC}"

# Create README.md if it doesn't exist (required by pyproject.toml)
if [ ! -f "README.md" ]; then
    echo -e "${YELLOW}⚠️  Creating README.md...${NC}"
    echo "# FP Dataset Generator

AI-powered dataset generation toolkit with web crawler integration.

## Features
- Dataset generation from web images
- AI-powered image processing
- Web crawler for custom searches

## Usage
Run \`./run_project.sh\` to start the application." > README.md
fi

if [ "$USE_PIP" = true ]; then
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install -q rich requests pillow streamlit scikit-learn openai python-dotenv
    echo -e "${GREEN}✓ Dependencies installed with pip${NC}"
else
    poetry install --no-root
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}⚠️  Poetry install failed, trying with --no-root...${NC}"
        poetry install --no-root
    fi
    echo -e "${GREEN}✓ Dependencies installed with poetry${NC}"
fi

# 4. Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "\n${YELLOW}⚠️  Creating base .env file...${NC}"
    echo "OPENAI_API_KEY=your_api_key_here" > .env
    echo "OPENAI_MODEL=gpt-5-nano" >> .env
    echo -e "${YELLOW}Please edit the .env file with your API Key.${NC}"
fi

# 5. Run main Python application
echo -e "\n${BLUE}[4/4] Running Application...${NC}"
echo -e "${GREEN}✓ Launching main.py...${NC}\n"

if [ "$USE_PIP" = true ]; then
    python3 main.py "$@"
else
    poetry run python main.py "$@"
fi

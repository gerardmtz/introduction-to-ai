#!/bin/bash

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Iniciando AI Dataset Generator Toolchain...${NC}"

# 1. Verificar dependencias
echo -e "\n${BLUE}[1/4] Verificando entorno...${NC}"
if ! command -v go &> /dev/null; then
    echo -e "${RED}❌ Go no está instalado. Por favor instala Go.${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 no está instalado.${NC}"
    exit 1
fi

if ! command -v poetry &> /dev/null; then
    echo -e "${YELLOW}⚠️  Poetry no encontrado. Intentando instalar dependencias con pip...${NC}"
    USE_PIP=true
else
    USE_PIP=false
fi

# 2. Compilar Crawler en Go
echo -e "\n${BLUE}[2/4] Compilando Web Crawler (Go)...${NC}"

# Verificar si existe el directorio webcrawler-source
if [ -d "webcrawler-source" ] && [ -f "webcrawler-source/main.go" ]; then
    cd webcrawler-source
    
    # Compilar el proyecto Go
    go build -o webcrawler .
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Build de Go exitoso: ./webcrawler-source/webcrawler${NC}"
        cd ..
    else
        echo -e "${RED}❌ Falló el build de Go.${NC}"
        cd ..
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  No se encontró el directorio webcrawler-source o main.go${NC}"
    echo -e "${YELLOW}   Continuando sin compilar el webcrawler...${NC}"
fi

# 3. Instalar dependencias Python
echo -e "\n${BLUE}[3/4] Configurando Python...${NC}"

# Crear README.md si no existe (requerido por pyproject.toml)
if [ ! -f "README.md" ]; then
    echo -e "${YELLOW}⚠️  Creando README.md...${NC}"
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
    echo -e "${GREEN}✓ Dependencias instaladas con pip${NC}"
else
    poetry install --no-root
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}⚠️  Poetry install falló, intentando con --no-root...${NC}"
        poetry install --no-root
    fi
    echo -e "${GREEN}✓ Dependencias instaladas con poetry${NC}"
fi

# 4. Crear .env si no existe
if [ ! -f ".env" ]; then
    echo -e "\n${YELLOW}⚠️  Creando archivo .env base...${NC}"
    echo "OPENAI_API_KEY=tu_api_key_aqui" > .env
    echo "OPENAI_MODEL=gpt-5-mini" >> .env
    echo -e "${YELLOW}Por favor edita el archivo .env con tu API Key.${NC}"
fi

# 5. Ejecutar aplicación principal (Python)
echo -e "\n${BLUE}[4/4] Ejecutando Aplicación...${NC}"
echo -e "${GREEN}✓ Lanzando main.py...${NC}\n"

if [ "$USE_PIP" = true ]; then
    python3 main.py "$@"
else
    poetry run python main.py "$@"
fi

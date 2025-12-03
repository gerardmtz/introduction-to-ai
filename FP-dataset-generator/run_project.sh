#!/bin/bash

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Iniciando AI Dataset Generator Toolchain...${NC}"

# 1. Verificar dependencias
echo -e "\n${BLUE}[1/4] Verificando entorno...${NC}"
if ! command -v go &> /dev/null; then
    echo "❌ Go no está instalado. Por favor instala Go."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no está instalado."
    exit 1
fi

if ! command -v poetry &> /dev/null; then
    echo "⚠️ Poetry no encontrado. Intentando instalar dependencias con pip..."
    USE_PIP=true
else
    USE_PIP=false
fi

# 2. Compilar Crawler en Go
echo -e "\n${BLUE}[2/4] Compilando Web Crawler (Go)...${NC}"
cd webcrawler-source || cd . # Intenta entrar a subcarpeta si existe, si no se queda en root (depende de estructura exacta)
# Asumiendo que los archivos go están en el root según el prompt file list
if [ -f "main.go" ]; then
    go build -o webcrawler-source main.go crawler.go downloader.go utils.go
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Build de Go exitoso: ./webcrawler-source${NC}"
    else
        echo "❌ Falló el build de Go."
        exit 1
    fi
else
    echo "⚠️ No se encontraron archivos Go en el directorio actual."
fi

# 3. Instalar dependencias Python
echo -e "\n${BLUE}[3/4] Configurando Python...${NC}"
if [ "$USE_PIP" = true ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install rich requests pillow streamlit scikit-learn openai python-dotenv
else
    poetry install
fi

# 4. Crear .env si no existe
if [ ! -f ".env" ]; then
    echo -e "\n${BLUE}⚠️ Creando archivo .env base...${NC}"
    echo "OPENAI_API_KEY=tu_api_key_aqui" > .env
    echo "OPENAI_MODEL=gpt-4o-mini" >> .env
    echo "Por favor edita el archivo .env con tu API Key."
fi

# 5. Ejecutar
echo -e "\n${BLUE}[4/4] Ejecutando Aplicación...${NC}"
if [ "$USE_PIP" = true ]; then
    python3 main.py
else
    poetry run python main.py
fi

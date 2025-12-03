# 🚀 AI Dataset Generator & Crawler Suite - Onboarding

Bienvenido al proyecto. Esta herramienta es un CLI híbrido (Python/Go) diseñado para automatizar la creación de Datasets de ML. Incluye un asistente de IA impulsado por modelos "Nano" (optimizados) para interpretar comandos en lenguaje natural.

## 📋 Prerrequisitos

Antes de iniciar, asegúrate de tener instalado:

1.  **Python 3.12+**: [Descargar](https://www.python.org/downloads/)
2.  **Go 1.21+**: [Descargar](https://go.dev/dl/)
3.  **Poetry** (Gestor de dependencias Python):
    ```bash
    curl -sSL [https://install.python-poetry.org](https://install.python-poetry.org) | python3 -
    ```
4.  **OpenAI API Key**: Necesaria para la funcionalidad de chat.

## ⚙️ Configuración del Entorno

### 1. Variables de Entorno
Crea un archivo `.env` en la raíz del proyecto:

```bash
OPENAI_API_KEY=sk-tu-clave-secreta-aqui
OPENAI_MODEL=gpt-4o-mini  # Usamos este como proxy para el concepto de gpt-5-nano
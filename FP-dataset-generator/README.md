# 🎨 AI Dataset Generator & Web Crawler Suite

> AI-powered toolkit for automated ML dataset generation with intelligent web crawling capabilities

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Go](https://img.shields.io/badge/go-1.21+-00ADD8.svg)](https://go.dev/dl/)

## 📖 Overview

A hybrid Python/Go command-line toolkit that automates the creation of machine learning datasets from web images. Features include:

- 🖼️ **Automated Image Collection** - Download images from Openverse with smart pagination
- 🤖 **AI Assistant** - Natural language interface powered by GPT models
- 🕷️ **Web Crawler** - Custom Go-based crawler for targeted web scraping
- 🎨 **Image Processing** - Automatic resizing, optimization, and validation
- 📊 **Dataset Organization** - Automatic train/val/test splitting with metadata generation
- 💬 **Interactive CLI** - Beautiful terminal interface with Rich library

## 🚀 Quick Start

### Prerequisites

Before running the project, ensure you have:

1. **Python 3.12+** - [Download here](https://www.python.org/downloads/)
2. **Go 1.21+** - [Download here](https://go.dev/dl/)
3. **Poetry** (Python dependency manager) - Install with:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```
4. **OpenAI API Key** - Required for AI Assistant functionality ([Get one here](https://platform.openai.com/api-keys))

### Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd FP-dataset-generator
   ```

2. **Configure environment variables:**
   
   Create a `.env` file in the project root:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-5-nano
   ```
   
   > **Note:** Replace `your_openai_api_key_here` with your actual OpenAI API key

3. **Run the setup script:**
   
   The `run_project.sh` script handles everything automatically:
   ```bash
   chmod +x run_project.sh  # Make script executable (first time only)
   ./run_project.sh
   ```
   
   This script will:
   - ✅ Verify all dependencies (Go, Python, Poetry)
   - ✅ Compile the Go web crawler
   - ✅ Install Python dependencies via Poetry
   - ✅ Create `.env` file if missing
   - ✅ Launch the interactive application

## 💡 Usage

### Interactive Mode

After running `./run_project.sh`, you'll see a menu with three options:

```
1. 🎨 Dataset Generator     - Create ML datasets from web images
2. 🕷️  Web Crawler AI        - Launch web crawler with custom search
3. 🤖 AI Assistant          - Chat with the tools (natural language)
4. ❌ Exit                  - Close the application
```

### Option 1: Dataset Generator (Interactive)

Follow the prompts to configure your dataset:
- Search query (e.g., "orange cats")
- Number of images
- Dataset name
- Advanced options (image size, quality, etc.)

### Option 2: Web Crawler

Launch the Go-based web crawler for custom web scraping:
- Specify search keywords
- Set number of pages to crawl
- Enable verbose logging

### Option 3: AI Assistant (Natural Language)

Use natural language to control the tools:

```
You: Generate a dataset of 50 orange cats with 70% train, 15% val, 15% test
🤖: Creating dataset configuration from your request...
```

```
You: Scrap 10 pages about machine learning
🤖: Preparing web crawler...
```

### Command-Line Mode (Direct)

You can also use the dataset generator directly from the command line:

```bash
./run_project.sh -q "orange cats" -n 50 --name "Orange Cats Dataset"
```

**Available arguments:**
- `-q, --query` - Search query for images
- `-n, --num` - Number of images to download
- `--name` - Dataset name
- `-d, --description` - Dataset description
- `-o, --output` - Output directory (default: `data/processed`)
- `-s, --size` - Image size in pixels (default: 256)
- `--quality` - JPEG quality 1-100 (default: 90)
- `--train-ratio` - Training set ratio (default: 0.7)
- `--val-ratio` - Validation set ratio (default: 0.15)
- `--test-ratio` - Test set ratio (default: 0.15)
- `--seed` - Random seed (default: 42)
- `--keep-temp` - Keep temporary files
- `--min-size` - Minimum image size (default: 100)

## 📁 Project Structure

```
FP-dataset-generator/
├── data/
│   ├── processed/          # Final datasets
│   ├── raw/                # Raw downloads
│   └── temp/               # Temporary processing files
├── src/
│   ├── ai_agent.py         # AI assistant logic
│   ├── pipeline.py         # Main dataset pipeline
│   ├── downloaders/        # Image download modules
│   ├── processors/         # Image processing modules
│   ├── organizers/         # Dataset organization
│   └── exporters/          # Metadata generation
├── webcrawler-source/      # Go web crawler
│   ├── main.go
│   ├── crawler.go
│   └── ...
├── main.py                 # Application entry point
├── run_project.sh          # Setup & run script
├── pyproject.toml          # Python dependencies
└── .env                    # Environment variables
```

## 🔧 Features in Detail

### Smart Image Download
- Automatic pagination to avoid rate limiting
- Intelligent retry logic
- Image validation and format conversion
- Progress tracking and error handling

### Image Processing Pipeline
1. **Download** - Fetch images from Openverse API
2. **Process** - Resize, optimize, and validate
3. **Organize** - Split into train/val/test sets
4. **Export** - Generate metadata and documentation

### AI Assistant Capabilities
- Natural language understanding for tool configuration
- Automatic parameter inference
- Smart defaults for missing values
- Tool selection based on user intent

## 🐛 Troubleshooting

### "Go is not installed"
Install Go from [go.dev/dl](https://go.dev/dl/)

### "Poetry not found"
The script will automatically fall back to pip. To install Poetry:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### "401 Unauthorized" from Openverse
This typically happens with large batch requests. The pagination system automatically handles this, but you can also:
- Request fewer images per batch
- Add delays between requests
- Register for Openverse API credentials (optional)

### Web Crawler Not Found
Ensure the Go build succeeded:
```bash
cd webcrawler-source
go build -o webcrawler .
cd ..
```

### Missing Dependencies
Run the setup script again:
```bash
./run_project.sh
```

Or manually install Python dependencies:
```bash
poetry install --no-root
# or
pip install rich requests pillow scikit-learn openai python-dotenv
```

## 📊 Output Format

Generated datasets include:

```
your-dataset/
├── train/
│   └── category_name/
│       ├── image_0001.jpg
│       ├── image_0002.jpg
│       └── ...
├── val/
│   └── category_name/
│       └── ...
├── test/
│   └── category_name/
│       └── ...
├── dataset_info.json       # Metadata and statistics
└── README.md               # Dataset documentation
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 🙏 Acknowledgments

- [Openverse](https://openverse.org/) - For providing free access to creative commons images
- [Rich](https://github.com/Textualize/rich) - For beautiful terminal formatting
- OpenAI - For GPT models powering the AI assistant

## 📞 Support

If you encounter any issues or have questions:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Review existing GitHub issues
3. Create a new issue with detailed information about your problem

---

Made with ❤️ for ML Engineers

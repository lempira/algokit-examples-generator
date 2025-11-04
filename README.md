# AlgoKit Examples Generator

AI-powered system to convert test files into runnable user-facing examples.

## Overview

The AlgoKit Examples Generator automatically analyzes test files in a repository and generates clean, well-documented, runnable examples for end users. It uses AI agents powered by Claude to understand test code and transform it into production-ready examples.

## Features

- **Automatic Discovery**: Scans repository for test files
- **AI-Powered Analysis**: Extracts and analyzes test blocks using Claude
- **Intelligent Planning**: Plans example generation based on user value
- **Code Generation**: Creates complete examples with documentation
- **Quality Assurance**: Validates examples for correctness
- **Iterative Refinement**: Automatically fixes issues (up to 3 iterations)

## Installation

```bash
# Clone the repository
git clone https://github.com/algorandfoundation/algokit-examples-generator
cd algokit-examples-generator

# Install with uv (recommended)
uv sync

# Or install with pip
pip install -e .
```

## Quick Start

```bash
# 1. Create a .env file with your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 2. Generate examples from current directory
uv run algokit-examples-gen

# 3. Generate examples from specific repository
uv run algokit-examples-gen /path/to/repository

# 4. Use specific LLM model
uv run algokit-examples-gen --model anthropic:claude-3-5-sonnet-20241022

# 5. Specify custom output directory
uv run algokit-examples-gen --output ./my-examples

# 6. Test with limited files for quick iteration
uv run algokit-examples-gen --limit-files 3
```

## Usage

### Command Line Interface

**Note**: All CLI commands must be prefixed with `uv run` to use the virtual environment.

```
usage: uv run algokit-examples-gen [-h] [-o OUTPUT_PATH] [-m MODEL] [-v] [--verbose] [--limit-files N] [repo_path]

positional arguments:
  repo_path             Path to the repository (default: current directory)

options:
  -h, --help            show this help message and exit
  -o OUTPUT_PATH, --output OUTPUT_PATH
                        Output directory for examples (default: <repo>/examples)
  -m MODEL, --model MODEL
                        LLM model to use (default: anthropic:claude-3-5-sonnet-20241022)
  -v, --version         show program's version number and exit
  --verbose             Enable verbose output
  --limit-files N       Limit processing to first N files discovered (useful for testing)
```

**Examples:**

```bash
# Show version
uv run algokit-examples-gen --version

# Show help
uv run algokit-examples-gen --help

# Generate from current directory
uv run algokit-examples-gen

# Generate with verbose output
uv run algokit-examples-gen --verbose

# Test with limited files (useful for quick iteration)
uv run algokit-examples-gen --limit-files 3
```

### Python API

```python
from pathlib import Path
from src import create_workflow

# Create workflow
workflow = create_workflow(
    repo_path=Path("/path/to/repo"),
    examples_output_path=Path("./examples"),
    llm_model="anthropic:claude-3-5-sonnet-20241022",
    limit_files=3  # Optional: limit to first N files for testing
)

# Run workflow
state = workflow.run(repository_name="my-repo")

# Access results
print(f"Generated {state.generation_data.summary.generated} examples")
```

## Workflow Phases

The generator runs through 6 phases:

### Phase 1: Discovery
Scans the repository for test files and calculates file hashes for incremental processing.

### Phase 2: Extraction
Analyzes test files and extracts test blocks with metadata (features, complexity, target users, etc.).

### Phase 3: Distillation
Plans which examples to generate based on test block analysis and user value.

### Phase 4: Generation
Generates complete example files including:
- `main.ts` - Clean example code
- `package.json` - Dependencies and scripts
- `tsconfig.json` - TypeScript configuration
- `README.md` - Complete documentation
- `.env.example` - Environment variables
- `artifacts/` - Required contracts/configs

### Phase 5: Quality Assurance
Validates generated examples for:
- Completeness (all required files)
- API usage (correct imports, no algosdk)
- Language compliance (no test scaffolding)
- Artifacts (functional artifacts)
- Runability (examples execute successfully)

### Phase 6: Refinement
Automatically fixes issues found in quality checks. Runs up to 3 iterations of Quality→Refinement until all examples pass or max iterations reached.

## Configuration

The application loads settings from a `.env` file in the project root. Create this file by copying `.env.example`:

```bash
cp .env.example .env
```

### Environment Variables

The `.env` file supports the following configuration:

```bash
# API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here  # Required for default model
OPENAI_API_KEY=your_openai_api_key_here        # Optional
GOOGLE_API_KEY=your_google_api_key_here        # Optional
GROQ_API_KEY=your_groq_api_key_here            # Optional

# Repository Settings
REPO_PATH=.                                     # Default repository path
EXAMPLES_OUTPUT_PATH=./examples                 # Default output directory

# LLM Configuration
DEFAULT_MODEL=anthropic:claude-3-5-sonnet-20241022  # Default model
TEMPERATURE=0.7                                     # LLM temperature (0.0-1.0)

# Processing Settings
MAX_REFINEMENT_ITERATIONS=3                     # Max refinement iterations
DISCOVERY_PATHS=src                             # Comma-separated subdirs to search (default: src)
# DISCOVERY_PATHS=src,tests                     # Example: search multiple directories
```

**Note**: CLI arguments override environment variables. For example:
- `uv run algokit-examples-gen --model openai:gpt-4` overrides `DEFAULT_MODEL`
- `uv run algokit-examples-gen --output /custom/path` overrides `EXAMPLES_OUTPUT_PATH`

### LLM Models

Supports any pydantic-ai compatible model:
- `anthropic:claude-3-5-sonnet-20241022` (default)
- `anthropic:claude-3-opus-20240229`
- `openai:gpt-4-turbo`
- `gemini-1.5-pro`

## Output Structure

```
examples/
├── 01-basic-transaction/
│   ├── main.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── README.md
│   └── .env.example
├── 02-deploy-contract/
│   ├── main.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── README.md
│   ├── .env.example
│   └── artifacts/
│       ├── approval.teal
│       └── clear.teal
├── 01-discovery.json
├── 02-extraction.json
├── 03-distillation.json
├── 04-generation.json
└── 05-quality.json
```

## Development

### Setup

```bash
# Install dependencies
uv sync

# Run linting
uv run ruff check src/ tests/

# Fix linting issues
uv run ruff check --fix src/ tests/

# Format code
uv run ruff format src/ tests/
```

### Testing

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_discovery.py

# Run with coverage
uv run pytest --cov=src tests/
```

## Architecture

The system uses:
- **pydantic-ai**: AI agents for code analysis and generation
- **pydantic**: Type-safe data models
- **pydantic-graph**: Workflow orchestration (future)
- **ruff**: Fast Python linting and formatting

### Key Components

- `src/agents/`: AI agents for each phase
- `src/nodes/`: Workflow nodes for phase execution
- `src/models/`: Pydantic models for structured data
- `src/utils/`: Utility functions (file I/O, execution, etc.)
- `src/workflow.py`: Main workflow orchestration
- `src/cli.py`: Command-line interface

## Incremental Processing

The generator supports incremental updates:
- Only processes changed test files
- Keeps unchanged examples
- Marks deleted examples for removal
- Regenerates only what's needed

This makes it fast for iterative development!

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run linting and tests
6. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- Documentation: https://github.com/algorandfoundation/algokit-examples-generator
- Issues: https://github.com/algorandfoundation/algokit-examples-generator/issues
- AlgoKit: https://github.com/algorandfoundation/algokit-cli

## Acknowledgments

Built with:
- [pydantic-ai](https://github.com/pydantic/pydantic-ai) - AI agent framework
- [Claude](https://www.anthropic.com) - AI model
- [AlgoKit](https://github.com/algorandfoundation/algokit-cli) - Algorand development toolkit


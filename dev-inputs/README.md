# Development Inputs

This directory contains sample input files for testing individual workflow phases.

## Usage

Place JSON files from previous runs here to test individual phases:

- `01-discovery.json` - Input for extraction phase
- `02-extraction.json` - Input for distillation phase
- `03-distillation.json` - Input for generation phase
- `04-generation.json` - Input for quality phase
- `05-quality.json` - Input for refinement phase

## Creating Sample Inputs

### Option 1: Copy from a successful run
```bash
cp examples/01-discovery.json dev-inputs/
cp examples/02-extraction.json dev-inputs/
```

### Option 2: Create minimal test data
See the phase markdown files in `.claude/phases/` for the expected JSON structure.

## Running Individual Phases

```bash
# Run extraction with sample input
uv run python scripts/run_phase.py extraction \
  --repo /path/to/algokit-utils-ts \
  --input-dir dev-inputs \
  --output-dir dev-outputs

# Run distillation
uv run python scripts/run_phase.py distillation \
  --input-dir dev-inputs \
  --output-dir dev-outputs
```

See `scripts/run_phase.py --help` for more options.


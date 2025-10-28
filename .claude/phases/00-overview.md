# Shared Concepts and Global Rules

This document defines concepts, terminology, and rules used across all phases of the test-to-example extraction process.

---

## Glossary

### File Status

The state of a test file relative to the previous run:

- `created`: New file not in previous discovery
- `updated`: Existing file with different hash
- `unchanged`: Existing file with same hash
- `deleted`: File in previous discovery but no longer exists

### Example Status

The state of a generated example (set in Phase 4 and updated in Phase 6):

- `generated`: Complete and runnable example
- `needs_review`: Has issues requiring attention (includes severity level)
- `error`: Could not be processed due to critical errors

### Distillation Status

The planning state of an example (used only in Phase 3):

- `planned`: Example is ready to be generated in Phase 4
- `keep`: Example is unchanged from previous run, no regeneration needed
- `delete`: Example's source test was deleted, should be removed

### Severity Levels

Classification of issues found during QA:

- `critical`: Example is completely broken or missing required components
- `high`: Incorrect usage or missing important prerequisites
- `medium`: Minor gaps or incomplete documentation
- `low`: Small improvements or cosmetic issues

### Complexity Levels

How difficult an example is for end users:

- `simple`: Basic, single-feature demonstration
- `moderate`: Multi-step workflow or configuration
- `complex`: Advanced usage, multiple features combined

### Example Potential

Likelihood that a test makes a good user-facing example:

- `high`: Clear, valuable, demonstrates important feature
- `medium`: Useful but niche or requires setup
- `low`: Too technical, edge case, or internal testing only

---

## Global Rules

### Output Location

All phase output files are saved in the `examples/` directory at the repository root:

- `examples/01-discovery.json`
- `examples/02-extraction.json`
- `examples/03-distillation.json`
- `examples/04-generation.json`
- `examples/05-quality.json`

Each file includes a `"timestamp"` field inside the JSON for traceability.

### Example ID Format

- **Format**: `NN-{slug}`

  - `NN`: two-digit numeric prefix, zero-padded (e.g. `01`, `02`)
  - `{slug}`: lowercase, hyphenated short name derived from title

- **Numbering order**:

  1. Sort by complexity (`simple` < `moderate` < `complex`)
  2. Within each complexity, sort alphabetically by title (case-insensitive)
  3. Assign sequential numbers starting from `01`

- **Example folder name** must match the `example_id` (e.g., `examples/01-basic-payment/`)

### Example Folder Structure

Each example uses a consistent layout:

```
examples/
  01-example-name/
    main.<ext>              # Main code file
    package.json            # Dependencies (or requirements.txt, go.mod, etc.)
    .env.example            # Environment variables template
    README.md               # Documentation
    artifacts/              # Helper files (contracts, configs, data)
```

### Example Isolation Requirements

Each example must be **completely self-contained**:

- Use only public/exported APIs of the package
- Have its own dependency file (package.json, requirements.txt, etc.)
- Include its own artifacts in `artifacts/` subfolder
- Not reference files from other examples or repository internals

### Incremental Processing

- **First run**: Process all test files
- **Subsequent runs**: Only process changed test files (detected via SHA-256 hash comparison)
- **First run detection**: A run is a first run if `01-discovery.json` does not exist

### Artifact Handling

When an example needs a file (contract, config, data):

1. Search the repository thoroughly
2. If found: Copy to example's `artifacts/` folder
3. If not found: Generate a minimal but **functional** artifact (no placeholders or stubs)

---

## Success Criteria

The process is successful when:

- All test files are discovered and processed
- At least 80% of examples have status `generated`
  - Formula: `(examples with status "generated") / (total examples) >= 0.80`
- All outputs are deterministic and reproducible
- Each example has clear documentation and traceability to source tests

# Test-to-Example Extraction Process

Generate runnable user examples from repository tests. Works on first run and incrementally on subsequent runs.

---

## How to Trigger

To execute this process, use one of these commands:

- **"Execute the test-to-example extraction process"**
- **"Run all phases from CLAUDE.md"**
- **"Run the complete test-to-example extraction process"**

---

## What This Does

Converts your test files into user-facing examples that demonstrate your library's capabilities.

**First run**: Process all tests → generate all examples
**Subsequent runs**: Only process changed tests → update affected examples

---

## Phase Execution Flow

```
Phase 1: Discovery
    ↓
Phase 2: Extraction
    ↓
Phase 3: Distillation
    ↓
Phase 4: Generation
    ↓
Phase 5: Quality Assurance
    ↓
    ├─→ [Issues found?] → Phase 6: Refinement → back to Phase 5 (max 3 times)
    └─→ [No issues] → Done
```

### Phase 1: Discovery

**Purpose**: Find all test files and track changes

**Input**: Repository files, previous `01-discovery.json` (if exists)

**Output**: `examples/01-discovery.json`

**Details**: [phases/01-discovery.md](phases/01-discovery.md)

---

### Phase 2: Extraction

**Purpose**: Analyze test blocks for example potential

**Input**: `01-discovery.json`, test files, previous `02-extraction.json` (if exists)

**Output**: `examples/02-extraction.json`

**Details**: [phases/02-extraction.md](phases/02-extraction.md)

---

### Phase 3: Distillation

**Purpose**: Analyze test blocks and plan which examples to create

**Input**: `02-extraction.json`, previous `03-distillation.json` (if exists)

**Output**: `examples/03-distillation.json` (example metadata and generation plan)

**Details**: [phases/03-distillation.md](phases/03-distillation.md)

---

### Phase 4: Generation

**Purpose**: Generate runnable example files from the distillation plan

**Input**: `03-distillation.json`, test files, previous `04-generation.json` (if exists)

**Output**:

- `examples/04-generation.json`
- Example folders: `examples/01-example-name/`, `examples/02-another-example/`, etc.

**Details**: [phases/04-generation.md](phases/04-generation.md)

---

### Phase 5: Quality Assurance

**Purpose**: Validate examples work correctly

**Input**: `04-generation.json`, example folders

**Output**: `examples/05-quality.json`

**Next step**:

- If issues found → automatically trigger Phase 6
- If no issues → process complete

**Details**: [phases/05-quality.md](phases/05-quality.md)

---

### Phase 6: Refinement (Optional)

**Purpose**: Automatically fix issues found in Phase 5

**Input**: `05-quality.json`, `04-generation.json`, example folders

**Output**:

- Updated `04-generation.json`
- Fixed example folders

**Next step**: Automatically run Phase 5 again to validate fixes

**Runs when**: Phase 5 finds critical/high issues or >20% examples need review

**Max iterations**: 3 Phase 5→6→5 cycles

**Details**: [phases/06-refinement.md](phases/06-refinement.md)

---

## Shared Concepts

See [phases/00-overview.md](phases/00-overview.md) for:

- Terminology (file status, example status, severity levels)
- Global rules (output location, ID format, folder structure)
- Example isolation requirements
- Success criteria

---

## Output Files

All outputs are saved in `examples/`:

```
examples/
  01-discovery.json           # Test file inventory
  02-extraction.json          # Test block analysis
  03-distillation.json        # Example metadata and generation plan
  04-generation.json          # Generation status
  05-quality.json             # Validation results
  EXECUTION_REPORT.md         # Final summary report (generated at process completion)
  01-basic-example/           # Generated example folder
    main.ts
    package.json
    tsconfig.json
    .env.example
    README.md
    artifacts/
  02-another-example/         # Another generated example
    ...
  phases/                     # Phase documentation
    00-overview.md
    01-discovery.md
    02-extraction.md
    03-distillation.md
    04-generation.md
    05-quality.md
    06-refinement.md
```

---

## Success Criteria

The process succeeds when:

- All test files are discovered and processed
- At least 80% of examples have status `generated` (working)
- Each example has clear documentation
- Examples are runnable or clearly document what's needed to run

---

## Execution Notes

When running this process:

1. **Always run phases in order**: 1 → 2 → 3 → 4 → 5 → (6 if needed)
2. **Incremental processing**: Only changed tests are reprocessed on subsequent runs
3. **Automatic refinement**: Phase 6 runs automatically if Phase 5 finds issues
4. **Maximum iterations**: Refinement loop stops after 3 cycles or when no more progress is made
5. **Full transparency**: All outputs are deterministic JSON files you can inspect

---

## Quick Start

1. Say: **"Execute the test-to-example extraction process"**
2. Wait for all phases to complete
3. Check `examples/` folder for generated examples
4. Review `EXECUTION_REPORT.md` for the complete summary
5. Review `05-quality.json` for detailed validation results

To update examples after changing tests, just run the process again. Only changed tests will be reprocessed.

---

## Final Report

At the end of the process, a comprehensive `EXECUTION_REPORT.md` is automatically generated with:
- Executive summary of all metrics
- Quality results across all refinement iterations
- Complete list of passing examples
- Details on examples needing manual review
- Recommendations for next steps

This report is generated when the process completes (either successfully or after max iterations).

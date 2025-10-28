# Phase 5: Quality Assurance

## Purpose

Validate generated examples to ensure they are complete, accurate, and runnable.

---

## Input

- `examples/04-generation.json` (from Phase 4)
- Example folders from `examples/NN-example-name/`

---

## Output

`examples/05-quality.json` containing:

- Validation results for each example
- Issues found with severity levels
- Decision on whether to trigger Phase 6 (refinement)

---

## Tasks

### 1. Determine Which Examples to Validate

**Validate**:

- Examples that were generated or regenerated in Phase 4
- Examples with status `generated` or `needs_review`

**Skip**:

- Examples that were kept unchanged in Phase 4

### 2. Run Validation Checks

For each example to validate:

#### A. Completeness Check

- [ ] All required files exist (main file, package.json, README.md)
- [ ] README has clear instructions
- [ ] Prerequisites are documented
- [ ] Environment variables are in .env.example

#### B. API Usage Check

- [ ] Code uses only public/exported APIs
- [ ] No imports from internal repository files
- [ ] Dependencies in package.json match actual imports

#### C. Language Compliance Check

Run language-specific static analysis and type checking to ensure code quality.

**IMPORTANT**: Before running any language checks, install dependencies first to ensure accurate validation results.

**TypeScript/JavaScript:**
- [ ] Install dependencies: `npm install` or `yarn install`
- [ ] Run `tsc --noEmit` (TypeScript type checking)
- [ ] Verify no type errors or warnings
- [ ] Check for proper type annotations
- [ ] Validate tsconfig.json or jsconfig.json if present

**Python:**
- [ ] Install dependencies: `pip install -r requirements.txt` or `poetry install`
- [ ] Run `mypy` for type checking (if type hints present)
- [ ] Run `pylint` or `flake8` for linting
- [ ] Verify syntax with `python -m py_compile`
- [ ] Check for proper imports and module structure

**Go:**
- [ ] Install dependencies: `go mod download` or `go get`
- [ ] Run `go vet` for static analysis
- [ ] Run `gofmt -l` to check formatting
- [ ] Run `go build` to verify compilation
- [ ] Check for proper package declarations

**Rust:**
- [ ] Install dependencies: `cargo fetch`
- [ ] Run `cargo check` for compilation
- [ ] Run `cargo clippy` for linting
- [ ] Run `cargo fmt --check` for formatting
- [ ] Verify Cargo.toml dependencies

**Java:**
- [ ] Install dependencies: `mvn install` or `gradle build`
- [ ] Run `javac` for compilation
- [ ] Run static analysis tools (e.g., SpotBugs, PMD)
- [ ] Verify proper package structure
- [ ] Check Maven/Gradle configuration

**Other Languages:**
- [ ] Install dependencies using language-appropriate package manager
- [ ] Use language-appropriate linters and formatters
- [ ] Run compiler/interpreter syntax checks
- [ ] Verify language-specific best practices
- [ ] Check dependency declarations match usage

**Notes on Dependency Installation:**
- Dependencies should be installed in each example directory before validation
- Installation errors should be reported as `critical` severity issues
- Missing package manifests (package.json, requirements.txt, etc.) should be flagged
- Use appropriate package manager based on lockfiles present (npm/yarn/pnpm for JS/TS)

#### D. Artifact Check

- [ ] Required artifacts exist in `artifacts/` folder
- [ ] Generated artifacts are functional (not stubs)
- [ ] Artifact paths in code are correct

#### E. Runability Check

- [ ] Attempt to run the example (if possible)
- [ ] Document any runtime errors
- [ ] Verify expected output matches documentation

### 3. Classify Issues by Severity

For each issue found:

- **critical**: Example cannot run at all, missing required files, compilation/syntax errors, fails language compliance checks
- **high**: Incorrect API usage, broken prerequisites, significant type errors, linting errors that affect functionality
- **medium**: Minor issues, missing documentation, incomplete setup, style warnings, minor type inconsistencies
- **low**: Cosmetic issues, minor documentation improvements, formatting issues, optional linting suggestions

### 4. Determine Refinement Trigger

Set `should_trigger_refinement` to `true` if:

- Any `critical` or `high` severity issues found
- More than 20% of validated examples have status `needs_review`

Otherwise, set to `false`.

### 5. Generate Recommendations

Suggest improvements:

- Specific fixes for identified issues
- Missing examples for important features
- Documentation improvements

### 6. Generate Output

Save to `examples/05-quality.json` with:

- Timestamp
- Iteration number
- Validation results
- Issues found
- Refinement decision

---

## Iteration Logic

- This phase always runs after Phase 4
- If `should_trigger_refinement` is `true`, Phase 6 will run next
- Phase 6 will then trigger Phase 5 again (max 3 times total)

---

## Example Output

```json
{
  "timestamp": "2025-10-17T11:15:00Z",
  "repository": "algokit-utils-ts",
  "iteration": 1,
  "validation_results": {
    "examples_validated": 16,
    "passed": 14,
    "failed": 2,
    "validation_checks": {
      "completeness": {
        "passed": 16,
        "checks": ["All required files exist", "README has clear instructions", "Prerequisites documented", "Environment variables in .env.example"]
      },
      "api_usage": {
        "passed": 15,
        "checks": ["Code uses public APIs", "No internal imports", "Dependencies match imports"]
      },
      "language_compliance": {
        "passed": 14,
        "language": "typescript",
        "checks": ["TypeScript type checking", "No compilation errors", "Linting passed"]
      },
      "artifacts": {
        "passed": 2,
        "checks": ["Required artifacts exist", "Artifacts are functional", "Paths are correct"]
      }
    },
    "issues_by_example": [
      {
        "example_id": "05-advanced-feature",
        "issues": [
          {
            "type": "missing_env_var",
            "severity": "medium",
            "description": "INDEXER_SERVER not in .env.example but used in code",
            "recommendation": "Add INDEXER_SERVER to .env.example"
          }
        ]
      },
      {
        "example_id": "12-complex-workflow",
        "issues": [
          {
            "type": "type_error",
            "severity": "high",
            "description": "TypeScript error: Property 'send' does not exist on type 'AlgorandClient | undefined'",
            "recommendation": "Add null check or ensure client is properly initialized",
            "check": "language_compliance"
          }
        ]
      }
    ]
  },
  "severity_summary": {
    "critical": 0,
    "high": 1,
    "medium": 1,
    "low": 0,
    "total": 2
  },
  "should_trigger_refinement": true,
  "refinement_reason": "Found 1 high severity issue",
  "recommendations": [
    "Fix client initialization in example 12-complex-workflow",
    "Add missing environment variable to example 05-advanced-feature",
    "Consider adding example for asset management feature"
  ]
}
```

## Stopping Conditions

Refinement stops when:

- **Success**: No critical/high issues and <20% examples need review
- **Max iterations**: 3 Phase 5→6→5 cycles completed
- **No progress**: Issue count doesn't decrease after refinement

---

## Final Summary Report

When Phase 5 completes and determines that refinement should NOT be triggered (either due to success or max iterations reached), generate a comprehensive summary report at `examples/EXECUTION_REPORT.md`.

This report should include:

### Report Structure

```markdown
# Test-to-Example Extraction - Execution Report

**Status**: [SUCCESSFUL/COMPLETED WITH ISSUES]
**Date**: [ISO 8601 timestamp]
**Repository**: [repository name]

## Executive Summary

- Total Examples Generated: [count]
- Test Files Processed: [count]
- Test Blocks Analyzed: [count]
- Pass Rate: [percentage]
- Issue Reduction: [percentage across all iterations]

## Final Results

### Quality Metrics

[Table showing iteration-by-iteration metrics]

### Examples Status

- Passing All Checks: [count] ([percentage]%)
- Needing Manual Review: [count] ([percentage]%)

## Process Execution Timeline

[Brief summary of each phase with key results]

## Examples Ready to Use

[List of all passing examples with links]

## Examples Needing Manual Review

[List of failing examples with issues and recommended fixes]

## Success Criteria Assessment

[Checklist showing which criteria were met]

## Recommendations

[Actionable recommendations for the failing examples and future runs]

## Output Files

[List of all generated files with descriptions]
```

### When to Generate

Generate this report ONLY when:
1. Phase 5 sets `should_trigger_refinement: false` (success), OR
2. Phase 5 is on iteration 3 (max iterations reached)

This ensures the report is created at the end of the complete process, summarizing all phases and refinement iterations.

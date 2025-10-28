# Phase 6: Iterative Refinement

## Purpose

Automatically fix issues found in Phase 5 to improve example quality.

---

## Input

- `examples/05-quality.json` (from Phase 5)
- `examples/04-generation.json` (from Phase 4)
- Example folders from `examples/NN-example-name/`

---

## Output

- Updated `examples/04-generation.json` with fixes applied
- Updated example folders with corrected code/documentation
- Refinement history added to `04-generation.json`

---

## When This Phase Runs

Phase 6 runs automatically after Phase 5 **only if** Phase 5 sets `should_trigger_refinement: true`.

This happens when:

- Any `critical` or `high` severity issues found
- More than 20% of examples have status `needs_review`

---

## Tasks

### 1. Load QA Results

Read `05-quality.json` and extract:

- List of issues by example
- Severity levels
- Recommended fixes

### 2. Prioritize Fixes

Process issues in order of severity:

1. **Critical**: Missing files, broken examples
2. **High**: Runtime errors, incorrect API usage
3. **Medium**: Missing documentation, incomplete setup
4. **Low**: Minor improvements

### 3. Apply Fixes

For each issue:

#### Missing Environment Variables

- Add to `.env.example` with example values
- Update README.md prerequisites section

#### Runtime Errors

- Fix code in main file
- Verify imports and API usage
- Add error handling if needed

#### Missing Documentation

- Update README.md with clearer instructions
- Add comments to code

#### Incorrect API Usage

- Correct imports to use public APIs
- Fix method calls and parameters

#### Missing Artifacts

- Generate or find required files
- Add to `artifacts/` folder

### 4. Update Metadata

For each fixed example:

- If all issues resolved: set status to `generated`
- If some issues remain: keep status as `needs_review` with updated severity
- Update `notes` field with what was fixed

### 5. Record Refinement History

Add entry to `refinement_history` in `04-generation.json`:

```json
{
  "iteration": 1,
  "timestamp": "2025-10-17T11:30:00Z",
  "changes_applied": 3,
  "issues_resolved": ["Fixed client initialization in 12-complex-workflow", "Added missing INDEXER_SERVER to 05-advanced-feature"],
  "examples_updated": ["05-advanced-feature", "12-complex-workflow"]
}
```

### 6. Trigger Phase 5 Again

After applying fixes, automatically run Phase 5 to validate the improvements.

---

## Iteration Logic

This creates a refinement loop: **Phase 5 → Phase 6 → Phase 5 → ...**

**Maximum iterations**: 3 Phase 5→6→5 cycles

**Stop if**:

- Phase 5 finds no critical/high issues and <20% examples need review (success)
- 3 iterations completed (max reached)
- Issue count doesn't decrease after refinement (no progress)

---

## Stopping Conditions

### Success

Phase 5 validation passes:

- No critical or high severity issues
- Less than 20% of examples have status `needs_review`

### Max Iterations Reached

3 complete Phase 5→6→5 cycles have run. Remaining issues are documented in example `notes` fields for manual review.

### No Progress

The total number of issues (sum of all severities) stays the same or increases for 2 consecutive iterations.

---

## Example Refinement History

```json
{
  "refinement_history": [
    {
      "iteration": 1,
      "timestamp": "2025-10-17T11:30:00Z",
      "changes_applied": 3,
      "issues_resolved": [
        "Fixed client initialization in 12-complex-workflow",
        "Added INDEXER_SERVER to 05-advanced-feature .env.example",
        "Generated missing approval.teal artifact for 08-contract-call"
      ],
      "examples_updated": ["05-advanced-feature", "08-contract-call", "12-complex-workflow"],
      "issues_before": 5,
      "issues_after": 2
    },
    {
      "iteration": 2,
      "timestamp": "2025-10-17T11:45:00Z",
      "changes_applied": 2,
      "issues_resolved": ["Updated README instructions for 08-contract-call", "Fixed import path in 05-advanced-feature"],
      "examples_updated": ["05-advanced-feature", "08-contract-call"],
      "issues_before": 2,
      "issues_after": 0
    }
  ]
}
```

After iteration 2, Phase 5 finds 0 issues, so refinement stops successfully.

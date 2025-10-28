# Phase 1: Test Discovery

## Purpose
Build a complete inventory of test files in the repository and track changes.

---

## Input
- Repository file system
- Previous `examples/01-discovery.json` (if exists)

---

## Output
`examples/01-discovery.json` containing:
- List of all test files with paths and SHA-256 hashes
- File status for each: `created`, `updated`, `unchanged`, or `deleted`
- Summary statistics

---

## Tasks

### 1. Locate Test Files
Search the repository for test files using language-specific patterns:
- **TypeScript/JavaScript**: `*.test.ts`, `*.spec.ts`, `*.test.js`, `*.spec.js`
- **Python**: `test_*.py`, `*_test.py`
- **Go**: `*_test.go`
- **Ruby**: `*_test.rb`

Also search in common test directories: `tests/`, `test/`, `__tests__/`, `spec/`

### 2. Compute File Hashes
Calculate SHA-256 checksum for each discovered test file.

### 3. Determine File Status

**If first run** (no previous `01-discovery.json` exists):
- Mark all discovered files with status `created`

**If subsequent run** (previous `01-discovery.json` exists):
- Load previous discovery data
- For each currently discovered file:
  - If not in previous run: status = `created`
  - If in previous run with different hash: status = `updated`
  - If in previous run with same hash: status = `unchanged`
- For each file in previous run but not currently discovered:
  - Add to output with status = `deleted`

### 4. Generate Output
Save results to `examples/01-discovery.json` with:
- Timestamp
- Repository name
- Summary counts (total, created, updated, unchanged, deleted)
- Array of test file objects

---

## Iteration Logic
This phase runs once per execution. No iteration needed.

---

## Example Output

```json
{
  "timestamp": "2025-10-17T10:30:00Z",
  "repository": "algokit-utils-ts",
  "summary": {
    "total_files_discovered": 40,
    "total_files_tracked": 42,
    "created": 2,
    "updated": 5,
    "unchanged": 33,
    "deleted": 2
  },
  "test_files": [
    {
      "path": "tests/transaction.test.ts",
      "sha256": "abc123def456...",
      "status": "updated",
      "last_modified": "2025-10-15T14:22:00Z"
    },
    {
      "path": "tests/account.test.ts",
      "sha256": "789ghi012jkl...",
      "status": "unchanged",
      "last_modified": "2025-09-10T09:15:00Z"
    },
    {
      "path": "tests/deprecated_feature.test.ts",
      "sha256": "def456ghi789...",
      "status": "deleted",
      "last_modified": "2025-08-05T11:30:00Z"
    }
  ]
}
```

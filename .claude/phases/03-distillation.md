# Phase 3: Example Distillation

## Purpose
Analyze extracted test blocks and plan which examples to create, without generating actual files yet.

---

## Input
- `examples/02-extraction.json` (from Phase 2)
- Previous `examples/03-distillation.json` (if exists)

---

## Output
- `examples/03-distillation.json` containing example metadata and generation plan

---

## Tasks

### 1. Select Test Blocks
- Include only test blocks with `example_potential` = `high` or `medium`
- Include only test blocks with `feature_classification` = `user-facing` or `mixed`
- Prioritize test blocks that have clear `target_users` and `specific_use_case`
- Group related test blocks into single examples where appropriate:
  - Same `use_case_category`
  - Complementary `features_tested`
  - Same or overlapping `target_users`
- Always maintain mapping from test blocks to examples

### 2. Determine Which Examples to Generate

**If first run** (no previous `03-distillation.json` exists):
- Plan generation for all selected examples

**If subsequent run** (previous `03-distillation.json` exists):
- **Generate**: Examples from test blocks in files with status `created` or `updated`
- **Regenerate**: Examples with status `needs_review` from previous run
- **Keep**: Examples from test blocks in files with status `unchanged` (no action needed)
- **Delete**: Examples whose source test files have status `deleted`

### 3. Plan Example Structure

For each example to generate, use extraction metadata to plan the example:

#### A. Define Example Metadata
- **Title**: Based on `specific_use_case`
- **Summary**: Concise description of what the example demonstrates
- **Target Users**: From `target_users` field
- **Complexity**: `simple`, `moderate`, or `complex`
- **Use Case Category**: From `use_case_category`
- **Features to Demonstrate**: From `features_tested`

#### B. Plan Required Artifacts
If the example needs external files (contracts, configs, data):

1. **Search the repository** thoroughly (check `contracts/`, `artifacts/`, `fixtures/`, `data/`, etc.)
2. **Record findings**:
   - If found: Record path and mark for copying
   - If not found: Mark for generation in Phase 4

#### C. Identify Prerequisites
- Required tools (Node.js, AlgoKit CLI, etc.)
- Required libraries (always public packages only)
- Required environment variables
- Required services (LocalNet, TestNet, etc.)

### 4. Assign Example IDs
Sort all examples and assign IDs:
1. Group by complexity: `simple`, `moderate`, `complex`
2. Within each group, sort alphabetically by title
3. Assign sequential IDs: `01-example-name`, `02-another-example`, etc.

### 5. Set Example Status
For each example:
- **`planned`**: Example is planned and ready for generation in Phase 4
- **`keep`**: Example is unchanged and should be kept as-is
- **`delete`**: Example should be deleted (source test removed)

### 6. Generate Output
Save to `examples/03-distillation.json` with:
- Timestamp
- Repository name
- Array of example objects with metadata and generation plan
- Summary statistics
- Refinement history (empty on first run)

---

## Iteration Logic
This phase runs once per execution. Phase 6 (Refinement) may update the output and trigger regeneration.

---

## Example Output

```json
{
  "timestamp": "2025-10-21T11:00:00Z",
  "repository": "algokit-utils-ts",
  "examples": [
    {
      "example_id": "01-basic-transaction",
      "title": "Creating a Payment Transaction",
      "summary": "Demonstrates how to create and send a basic payment transaction",
      "language": "typescript",
      "complexity": "simple",
      "example_potential": "high",
      "use_case_category": "Transaction Management",
      "specific_use_case": "When the user wants to send ALGO from one account to another and wait for blockchain confirmation",
      "target_users": ["dApp developers", "Wallet developers", "Blockchain integrators"],
      "features_tested": ["makePaymentTxn", "sendTransaction", "waitForConfirmation"],
      "feature_tags": ["transactions", "payments"],
      "folder": "examples/01-basic-transaction",
      "prerequisites": {
        "tools": ["Node.js >= 18"],
        "libraries": ["@algorandfoundation/algokit-utils"],
        "environment": [
          {
            "name": "ALGOD_SERVER",
            "required": true,
            "example": "http://localhost:4001"
          },
          {
            "name": "ALGOD_TOKEN",
            "required": true,
            "example": "aaaa..."
          }
        ]
      },
      "run_instructions": {
        "install": ["npm install"],
        "execute": ["npm start"]
      },
      "expected_output": ["Transaction ID", "Confirmation"],
      "source_tests": [
        {
          "file": "tests/transaction.test.ts",
          "test_name": "creates a payment transaction"
        }
      ],
      "artifacts_plan": [],
      "status": "planned",
      "notes": ""
    },
    {
      "example_id": "02-deploy-contract",
      "title": "Deploying a Smart Contract",
      "summary": "Shows how to compile and deploy a smart contract",
      "language": "typescript",
      "complexity": "moderate",
      "example_potential": "high",
      "use_case_category": "Smart Contract Deployment",
      "specific_use_case": "When the user wants to deploy and initialize a smart contract application on Algorand",
      "target_users": ["Smart contract developers", "dApp developers", "DevOps engineers"],
      "features_tested": ["compileContract", "deployApplication", "initializeApp"],
      "feature_tags": ["smart-contracts", "deployment"],
      "folder": "examples/02-deploy-contract",
      "prerequisites": {
        "tools": ["Node.js >= 18", "AlgoKit CLI"],
        "libraries": ["@algorandfoundation/algokit-utils"]
      },
      "run_instructions": {
        "setup": ["algokit localnet start"],
        "install": ["npm install"],
        "execute": ["npm start"]
      },
      "expected_output": ["Contract compiled", "Application ID"],
      "source_tests": [
        {
          "file": "tests/deploy.test.ts",
          "test_name": "deploys application"
        }
      ],
      "artifacts_plan": [
        {
          "target_file": "artifacts/approval.teal",
          "type": "contract",
          "action": "generate",
          "source_path": null,
          "note": "No existing TEAL found - will generate minimal approval program"
        },
        {
          "target_file": "artifacts/clear.teal",
          "type": "contract",
          "action": "generate",
          "source_path": null,
          "note": "No existing TEAL found - will generate minimal clear program"
        }
      ],
      "status": "planned",
      "notes": "Will generate functional TEAL programs for demonstration"
    }
  ],
  "summary": {
    "total_examples": 2,
    "planned": 2,
    "keep": 0,
    "delete": 0,
    "complexity_breakdown": {
      "simple": 1,
      "moderate": 1,
      "complex": 0
    }
  },
  "refinement_history": []
}
```

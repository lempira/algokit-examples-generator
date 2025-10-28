# Phase 2: Test Block Extraction

## Purpose
Identify and analyze individual test blocks that could serve as end-user examples.

---

## Input
- `examples/01-discovery.json` (from Phase 1)
- Test files from the repository
- Previous `examples/02-extraction.json` (if exists)

---

## Output
`examples/02-extraction.json` containing:
- Analyzed test blocks from each test file
- Metadata: feature tested, complexity, example potential, prerequisites
- Summary statistics

---

## Tasks

### 1. Determine Which Files to Parse

**If first run** (no previous `02-extraction.json` exists):
- Parse all test files from `01-discovery.json`

**If subsequent run** (previous `02-extraction.json` exists):
- Parse only files with status `created` or `updated`
- Copy analysis for files with status `unchanged` from previous run
- Keep analysis for files with status `deleted` (change file_status to `deleted`)

### 2. Parse Test Files
For each test file to be parsed, detect test blocks based on language conventions:
- **TypeScript/JavaScript**: `test(...)`, `it(...)`, `describe(...)` blocks
- **Python**: `def test_*`, `@pytest.mark.*`
- **Go**: `func Test*`
- **Ruby**: `def test_*`, `describe` blocks

### 3. Analyze Each Test Block
For each test block, extract:
- **test_name**: The name of the test function/block
- **line_range**: Start and end line numbers
- **features_tested**: Array of specific features or capabilities being tested
  - List all features/APIs/methods demonstrated in the test
  - Be specific (e.g., "makePaymentTxn", "deployContract", "getAccountInfo")
- **feature_classification**: Whether these features are internal or user-facing
  - `user-facing`: Features exposed in public API that end users would use
  - `internal`: Implementation details, test utilities, or internal APIs
  - `mixed`: Contains both user-facing and internal features
- **use_case_category**: High-level category of the use case (only if user-facing or mixed)
  - Examples: "Transaction Management", "Account Operations", "Smart Contract Deployment",
    "Application State Management", "Asset Operations", "Testing & Development"
- **specific_use_case**: Concrete scenario description (only if user-facing or mixed)
  - Format: "When the user wants to [specific goal/action]..."
  - Example: "When the user wants to send ALGO from one account to another"
  - Example: "When the user wants to deploy and initialize a smart contract with custom parameters"
- **target_users**: Array of user types who would be interested (only if user-facing or mixed)
  - Examples: "dApp developers", "Smart contract developers", "DevOps engineers",
    "Blockchain integrators", "QA engineers", "Wallet developers", "DeFi builders"
- **example_potential**: `high`, `medium`, or `low`
  - High: Clear, valuable, demonstrates important user-facing feature
  - Medium: Useful but niche, requires setup, or demonstrates less common feature
  - Low: Too technical, edge case, internal testing only, or not useful to end users
- **complexity**: `simple`, `moderate`, or `complex`
  - Simple: Basic, single-feature demonstration
  - Moderate: Multi-step workflow or configuration
  - Complex: Advanced usage, multiple features combined
- **prerequisites**: What's needed to run this
  - imports: Required libraries
  - setup_requirements: Services, accounts, etc.
  - configuration: Environment variables, config files
- **key_concepts**: Main concepts demonstrated
- **user_value**: Why this would help an end user (only if user-facing or mixed; explain the practical benefit)

### 4. Generate Output
Save to `examples/02-extraction.json` with:
- Timestamp
- Repository name
- Summary statistics
- Array of test file analyses with test blocks

---

## Iteration Logic
This phase runs once per execution. No iteration needed.

---

## Example Output

```json
{
  "timestamp": "2025-10-17T10:45:00Z",
  "repository": "algokit-utils-ts",
  "summary": {
    "total_test_blocks": 247,
    "from_created_files": 15,
    "from_updated_files": 32,
    "from_unchanged_files": 195,
    "from_deleted_files": 5,
    "potential_breakdown": {
      "high": 89,
      "medium": 103,
      "low": 55
    },
    "complexity_breakdown": {
      "simple": 120,
      "moderate": 90,
      "complex": 37
    }
  },
  "test_analysis": [
    {
      "source_file": "tests/transaction.test.ts",
      "file_status": "updated",
      "test_blocks": [
        {
          "test_name": "creates a payment transaction",
          "line_range": "45-78",
          "features_tested": [
            "makePaymentTxn",
            "sendTransaction",
            "waitForConfirmation"
          ],
          "feature_classification": "user-facing",
          "use_case_category": "Transaction Management",
          "specific_use_case": "When the user wants to send ALGO from one account to another and wait for blockchain confirmation",
          "target_users": [
            "dApp developers",
            "Wallet developers",
            "Blockchain integrators"
          ],
          "example_potential": "high",
          "complexity": "simple",
          "prerequisites": {
            "imports": ["@algorandfoundation/algokit-utils"],
            "setup_requirements": ["Algorand client", "Two accounts"],
            "configuration": ["ALGOD_SERVER", "ALGOD_TOKEN"]
          },
          "key_concepts": ["transaction creation", "payment operations", "transaction confirmation"],
          "user_value": "Shows the most common operation users will perform - transferring ALGO between accounts with proper confirmation handling"
        },
        {
          "test_name": "handles transaction with note field",
          "line_range": "80-95",
          "features_tested": [
            "makePaymentTxn",
            "transaction.note"
          ],
          "feature_classification": "user-facing",
          "use_case_category": "Transaction Management",
          "specific_use_case": "When the user wants to attach metadata or messages to a transaction for tracking or communication purposes",
          "target_users": [
            "dApp developers",
            "DeFi builders",
            "Blockchain integrators"
          ],
          "example_potential": "medium",
          "complexity": "simple",
          "prerequisites": {
            "imports": ["@algorandfoundation/algokit-utils"],
            "setup_requirements": ["Algorand client"],
            "configuration": ["ALGOD_SERVER", "ALGOD_TOKEN"]
          },
          "key_concepts": ["transaction notes", "metadata", "transaction annotation"],
          "user_value": "Demonstrates how to add custom data to transactions for tracking, auditing, or communication between parties"
        },
        {
          "test_name": "internal utility function processes raw transaction data",
          "line_range": "100-115",
          "features_tested": [
            "_parseRawTransaction",
            "_validateTransactionFormat"
          ],
          "feature_classification": "internal",
          "example_potential": "low",
          "complexity": "simple",
          "prerequisites": {
            "imports": ["@algorandfoundation/algokit-utils"],
            "setup_requirements": ["Test fixtures"],
            "configuration": []
          },
          "key_concepts": ["transaction parsing", "data validation"],
          "user_value": null
        }
      ]
    }
  ]
}
```

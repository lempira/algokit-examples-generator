# Phase 4: Example Generation

## Purpose

Generate runnable example files based on the plan created in Phase 3 (Distillation).

---

## Input

- `examples/03-distillation.json` (from Phase 3)
- Test files from the repository
- Previous `examples/04-generation.json` (if exists)

---

## Output

- `examples/04-generation.json` containing generation status and metadata
- Example folders: `examples/NN-example-name/` with all required files

---

## Example Folder Structure

Each generated example MUST follow this structure:

```
examples/NN-example-name/
├── main.ts              # Main example code
├── package.json         # Package configuration
├── tsconfig.json        # TypeScript configuration
├── .env.example         # Environment variable template (optional)
├── README.md            # Example documentation
└── artifacts/           # Required artifacts (optional)
    ├── contract.teal
    ├── config.json
    └── ...
```

---

## Critical Generation Rules

### Rule 1: algokit-utils Import Path

**ALWAYS** import `@algorandfoundation/algokit-utils` from the `dist` folder:

```json
{
  "dependencies": {
    "@algorandfoundation/algokit-utils": "file:../../dist"
  }
}
```

**Why**: Examples run against the local build of the library, not the published npm package.

### Rule 2: Only algokit-utils Methods

**ONLY** use methods from `@algorandfoundation/algokit-utils`. **DO NOT** use `algosdk` methods directly.

**Allowed**:

```typescript
import { AlgorandClient } from '@algorandfoundation/algokit-utils'

const algorand = AlgorandClient.defaultLocalNet()
const sender = await algorand.account.fromEnvironment('SENDER')
const payment = await algorand.send.payment({...})
```

**NOT Allowed**:

```typescript
import algosdk from 'algosdk'
import type { Account } from 'algosdk'

// ❌ Don't use algosdk methods directly
const algodClient = new algosdk.Algodv2(...)
const txn = algosdk.makePaymentTxnWithSuggestedParamsFromObject(...)

// ❌ Don't import types from algosdk either
// Use types from @algorandfoundation/algokit-utils instead
```

### Rule 3: TypeScript Configuration

Always include a `tsconfig.json` with proper module resolution:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "esModuleInterop": true,
    "skipLibCheck": true,
    "strict": true,
    "resolveJsonModule": true
  },
  "include": ["*.ts"]
}
```

### Rule 4: Package Type

Always set `"type": "module"` in `package.json`:

```json
{
  "type": "module",
  "scripts": {
    "start": "tsx main.ts"
  },
  "devDependencies": {
    "tsx": "^4.7.0"
  }
}
```

---

## Tasks

### 1. Process Generation Plan

For each example in `03-distillation.json`:

**If status = `planned`**:

- Generate all example files (detailed below)
- Update status to `generated`, `needs_review`, or `error`

**If status = `keep`**:

- Skip generation, keep existing files
- Copy metadata to output

**If status = `delete`**:

- Remove example folder
- Record deletion in output

### 2. Transform Tests into Example Code

For each example to generate:

#### A. Extract Core Logic from Tests

1. **Locate source test files** from `source_tests` field
2. **Find test blocks** matching the test names
3. **Extract the actual usage code**:
   - Strip out `expect()`, `assert()`, `toBe()`, etc.
   - Remove `mock()`, `spy()`, test framework imports
   - Keep only the actual library usage

**Example transformation**:

```typescript
// From test file:
it('creates a payment transaction', async () => {
  const algod = algorandFixture.context.algod
  const sender = await getTestAccount('SENDER')
  const receiver = await getTestAccount('RECEIVER')

  const result = await algokit.sendPayment(
    {
      from: sender,
      to: receiver,
      amount: algokit.algos(5),
    },
    algod,
  )

  expect(result.txId).toBeDefined()
  expect(result.confirmation).toBeDefined()
})

// To example code:
import { AlgorandClient } from '@algorandfoundation/algokit-utils'

async function main() {
  // Initialize client
  const algorand = AlgorandClient.defaultLocalNet()

  // Get accounts
  const sender = await algorand.account.fromEnvironment('SENDER')
  const receiver = algorand.account.random()

  // Send payment
  const result = await algorand.send.payment({
    sender: sender.addr,
    receiver: receiver.addr,
    amount: (5).algo(),
  })

  console.log('Transaction ID:', result.txId)
  console.log('Confirmed in round:', result.confirmation.confirmedRound)
}

main().catch(console.error)
```

#### B. Add Helpful Comments

Add comments that explain:

- **What** each section does
- **Why** certain parameters are needed
- **How** to customize for different use cases

**Good example**:

```typescript
// Initialize AlgorandClient connected to LocalNet
const algorand = AlgorandClient.defaultLocalNet()

// Get sender account from environment variable
// This keeps private keys secure and out of code
const sender = await algorand.account.fromEnvironment('SENDER')

// Create a random receiver for this example
// In production, you'd use a real recipient address
const receiver = algorand.account.random()
```

#### C. Add Console Output

Add `console.log()` statements to show:

- Progress through the example
- Important values (transaction IDs, addresses, amounts)
- Results and confirmations

**Example**:

```typescript
console.log('=== Payment Transaction Example ===\n')
console.log('Sender:', sender.addr)
console.log('Receiver:', receiver.addr)
console.log('Amount:', (5).algo(), 'microAlgos')

const result = await algorand.send.payment({...})

console.log('\nTransaction sent!')
console.log('Transaction ID:', result.txId)
console.log('Confirmed in round:', result.confirmation.confirmedRound)
```

### 3. Generate Required Files

For each example, create these files:

#### main.ts

```typescript
import { AlgorandClient } from '@algorandfoundation/algokit-utils'
// Import other algokit-utils types as needed

async function main() {
  console.log('=== [Example Title] ===\n')

  // Example code here
  // - Use algokit-utils methods only
  // - Add helpful comments
  // - Add console output

  console.log('\n=== Complete ===')
}

main().catch(console.error)
```

#### package.json

```json
{
  "name": "algorand-[example-name]-example",
  "version": "1.0.0",
  "description": "[Example summary]",
  "type": "module",
  "scripts": {
    "start": "tsx main.ts"
  },
  "dependencies": {
    "@algorandfoundation/algokit-utils": "file:../../dist",
    "algosdk": "^3.5.2"
  },
  "devDependencies": {
    "tsx": "^4.7.0"
  }
}
```

**Important**:

- ALWAYS use `"@algorandfoundation/algokit-utils": "file:../../dist"`
- Include `algosdk` as a peer dependency (used internally by algokit-utils)
- Use `tsx` for running TypeScript directly

#### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "esModuleInterop": true,
    "skipLibCheck": true,
    "strict": true,
    "resolveJsonModule": true
  },
  "include": ["*.ts", "artifacts/**/*"]
}
```

#### .env.example (if environment variables are needed)

```env
# Algod Configuration (LocalNet defaults)
ALGOD_SERVER=http://localhost:4001
ALGOD_TOKEN=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa

# Account Mnemonics
SENDER_MNEMONIC=your sender account mnemonic here

# Optional: Indexer Configuration
INDEXER_SERVER=http://localhost:8980
INDEXER_TOKEN=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
```

#### README.md

````markdown
# [Example Title]

[Brief description of what this example demonstrates]

## Use Case

[Specific use case from distillation - "When you want to..."]

**Target Users**: [List of target user types]

## What This Example Shows

- [Key concept 1]
- [Key concept 2]
- [Key concept 3]

## Prerequisites

- Node.js >= 18
- [AlgoKit CLI](https://github.com/algorandfoundation/algokit-cli) (for LocalNet)
- [Other prerequisites if needed]

## Setup

1. **Start LocalNet** (if not already running):
   ```bash
   algokit localnet start
   ```
````

2. **Install dependencies**:

   ```bash
   npm install
   ```

3. **Configure environment** (if needed):
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

## Run

```bash
npm start
```

## Expected Output

```
=== [Example Title] ===

[Sample output showing what users should see]

=== Complete ===
```

## Features Demonstrated

- **[Feature 1]**: [Brief description from features_tested]
- **[Feature 2]**: [Brief description from features_tested]
- **[Feature 3]**: [Brief description from features_tested]

## Key Code Patterns

### [Pattern 1 Name]

```typescript
// Show important code snippet with explanation
const algorand = AlgorandClient.defaultLocalNet()
```

### [Pattern 2 Name]

```typescript
// Show another important pattern
const sender = await algorand.account.fromEnvironment('SENDER')
```

## Learn More

- [AlgoKit Utils Documentation](https://github.com/algorandfoundation/algokit-utils-ts)
- [Algorand Developer Portal](https://developer.algorand.org/)

````

### 4. Handle Artifacts

For each artifact in `artifacts_plan`:

**If action = `copy`**:
1. Copy file from `source_path` to example `artifacts/` folder
2. Verify file was copied successfully
3. Record in `generated_artifacts` with `"source": "copied"`

**If action = `generate`**:
1. Generate a **minimal but functional** artifact
2. Save to example `artifacts/` folder
3. Record in `generated_artifacts` with `"source": "generated"`

**Example generated TEAL contract** (minimal but functional):

```teal
#pragma version 8

// Minimal approval program
// Approves all transactions

int 1
return
````

### 5. Set Generation Status

For each example:

- **`generated`**: All files created successfully, example should work
- **`needs_review`**: Files created but may have issues (include severity and details)
- **`error`**: Could not generate files (include error message)

### 6. Generate Output

Save to `examples/04-generation.json`:

```json
{
  "timestamp": "2025-10-21T12:00:00Z",
  "repository": "algokit-utils-ts",
  "examples": [
    {
      "example_id": "01-basic-transaction",
      "title": "Creating a Payment Transaction",
      "folder": "examples/01-basic-transaction",
      "status": "generated",
      "generated_files": [
        "main.ts",
        "package.json",
        "tsconfig.json",
        "README.md"
      ],
      "generated_artifacts": [],
      "generation_notes": "",
      "source_tests": [...]
    }
  ],
  "summary": {
    "total_examples": 10,
    "generated": 8,
    "needs_review": 1,
    "error": 0,
    "kept_unchanged": 1,
    "deleted": 0
  }
}
```

---

## Quality Checklist

Before marking an example as `generated`, verify:

- [ ] `main.ts` imports ONLY from `@algorandfoundation/algokit-utils` (no algosdk imports at all, including types)
- [ ] `package.json` uses `"file:../../dist"` for algokit-utils
- [ ] `package.json` has `"type": "module"`
- [ ] `tsconfig.json` includes proper configuration
- [ ] All test scaffolding removed (no `expect`, `assert`, `mock`)
- [ ] Helpful comments explain what and why
- [ ] Console output shows progress and results
- [ ] README includes all required sections
- [ ] Required artifacts are present
- [ ] Code is clean, readable, and user-facing

---

## Common Pitfalls to Avoid

### ❌ Using algosdk directly

```typescript
// DON'T
import algosdk from 'algosdk'
const txn = algosdk.makePaymentTxnWithSuggestedParamsFromObject(...)
```

### ✅ Use algokit-utils instead

```typescript
// DO
import { AlgorandClient } from '@algorandfoundation/algokit-utils'
const algorand = AlgorandClient.defaultLocalNet()
const result = await algorand.send.payment({...})
```

### ❌ Wrong import path

```typescript
// DON'T
"@algorandfoundation/algokit-utils": "^7.0.0"
```

### ✅ Correct import path

```typescript
// DO
"@algorandfoundation/algokit-utils": "file:../../dist"
```

### ❌ Leaving test code

```typescript
// DON'T
expect(result.txId).toBeDefined()
const mockClient = vi.fn()
```

### ✅ User-facing code only

```typescript
// DO
console.log('Transaction ID:', result.txId)
```

---

## Iteration Logic

This phase runs once per execution. Phase 6 (Refinement) may update examples and trigger regeneration.

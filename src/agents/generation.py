"""Generation agent for creating example code from tests"""

import time

from pydantic import BaseModel
from pydantic_ai import Agent

from ..models.workflow import LLMConfig

AGENT_RETRIES = 3
MODEL_MAX_TOKENS = 20000


class GeneratedExample(BaseModel):
    """Generated example code and files"""

    main_code: str
    readme_content: str
    package_json: str
    tsconfig_json: str
    env_example: str | None = None


def create_generation_agent(llm_config: LLMConfig) -> Agent:
    """Create and configure the generation agent

    Args:
        llm_config: LLM configuration

    Returns:
        Configured pydantic-ai Agent
    """
    return Agent(
        llm_config.default_model,
        output_type=GeneratedExample,
        system_prompt=get_system_prompt(),
        retries=AGENT_RETRIES,
        model_settings={"max_tokens": MODEL_MAX_TOKENS},
    )


def get_system_prompt() -> str:
    """Get the system prompt for the generation agent"""
    return """You are an expert at transforming test code into clean, user-facing examples.

CRITICAL RULES (NEVER VIOLATE):
1. ONLY import from '@algorandfoundation/algokit-utils' - NEVER import algosdk or algosdk types
2. ALWAYS use "file:../../dist" for algokit-utils dependency in package.json
3. ALWAYS set "type": "module" in package.json
4. Strip ALL test scaffolding (expect, assert, mock, spy, test framework imports)
5. Add helpful comments explaining what and why
6. Add console.log statements to show progress and results
7. Use AlgorandClient.defaultLocalNet() pattern
8. Wrap everything in async main() function

TRANSFORMATION PROCESS:
1. Extract core logic from test code
2. Remove all test assertions and mocks
3. Replace test fixtures with real initialization
4. Add clear comments and console output
5. Make code production-ready and user-facing

EXAMPLE TRANSFORMATION:
From test:
```typescript
it('creates payment', async () => {
  const algod = fixture.algod
  const sender = await getTestAccount('SENDER')
  expect(result.txId).toBeDefined()
})
```

To example:
```typescript
import { AlgorandClient } from '@algorandfoundation/algokit-utils'

async function main() {
  console.log('=== Payment Transaction Example ===\\n')

  // Initialize client connected to LocalNet
  const algorand = AlgorandClient.defaultLocalNet()

  // Get sender from environment
  const sender = await algorand.account.fromEnvironment('SENDER')

  console.log('Transaction ID:', result.txId)
}

main().catch(console.error)
```

PACKAGE.JSON TEMPLATE:
```json
{
  "name": "algorand-[name]-example",
  "version": "1.0.0",
  "description": "[description]",
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

TSCONFIG.JSON TEMPLATE:
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
```"""


async def generate_example(
    agent: Agent,
    example_plan: dict,
    source_test_code: str,
) -> GeneratedExample:
    """Generate example code from test code

    Args:
        agent: Configured pydantic-ai Agent
        example_plan: Example plan from distillation
        source_test_code: Source test code to transform

    Returns:
        GeneratedExample with all files
    """
    # Prepare the prompt
    prompt = f"""Transform this test code into a clean, runnable example.

Example Plan:
- Title: {example_plan["title"]}
- Summary: {example_plan["summary"]}
- Use Case: {example_plan["specific_use_case"]}
- Features: {", ".join(example_plan["features_tested"])}
- Target Users: {", ".join(example_plan["target_users"])}
- Complexity: {example_plan["complexity"]}

Source Test Code:
```typescript
{source_test_code}
```

Generate:
1. main_code: Clean TypeScript example code (main.ts)
2. readme_content: Complete README.md with all sections
3. package_json: package.json with correct dependencies
4. tsconfig_json: tsconfig.json with proper config
5. env_example: .env.example if environment variables needed (or null)

Remember:
- NO algosdk imports (including types)
- Use AlgorandClient patterns
- Add helpful comments
- Add console output
- Remove all test code
- Make it user-facing and production-ready"""

    # Run the agent
    print("      🤖 Running generation agent...")
    start_time = time.time()

    try:
        result = await agent.run(prompt)
        elapsed_time = time.time() - start_time

        print(f"      ⏱️  Agent completed in {elapsed_time:.2f}s")

        usage = result.usage()
        print(
            f"      📊 Tokens: {usage.total_tokens} total "
            f"(request: {usage.request_tokens}, response: {usage.response_tokens})"
        )

        return result.output

    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"      ❌ Agent failed after {elapsed_time:.2f}s")
        print(f"      Error: {type(e).__name__}: {str(e)[:100]}")
        raise


def generate_example_sync(
    agent: Agent,
    example_plan: dict,
    source_test_code: str,
) -> GeneratedExample:
    """Synchronous version of generate_example"""
    import asyncio

    return asyncio.run(generate_example(agent, example_plan, source_test_code))

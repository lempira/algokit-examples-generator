"""Refinement agent for fixing issues in generated examples"""

import time

from pydantic import BaseModel
from pydantic_ai import Agent

from ..models.workflow import LLMConfig

AGENT_RETRIES = 3
MODEL_MAX_TOKENS = 20000


class RefinedFiles(BaseModel):
    """Refined example files"""

    main_code: str | None = None
    readme_content: str | None = None
    package_json: str | None = None
    env_example: str | None = None
    notes: str = ""


def create_refinement_agent(llm_config: LLMConfig) -> Agent:
    """Create and configure the refinement agent

    Args:
        llm_config: LLM configuration

    Returns:
        Configured pydantic-ai Agent
    """
    return Agent(
        llm_config.default_model,
        output_type=RefinedFiles,
        system_prompt=get_system_prompt(),
        retries=AGENT_RETRIES,
        model_settings={"max_tokens": MODEL_MAX_TOKENS},
    )


def get_system_prompt() -> str:
    """Get the system prompt for the refinement agent"""
    return """You are an expert code reviewer and fixer specializing in example refinement.

Your task is to fix issues in generated code examples based on quality feedback.

CRITICAL RULES (NEVER VIOLATE):
1. ONLY import from '@algorandfoundation/algokit-utils' - NEVER import algosdk or algosdk types
2. ALWAYS use "file:../../dist" for algokit-utils dependency in package.json
3. ALWAYS set "type": "module" in package.json
4. Remove ALL test scaffolding (expect, assert, mock, spy)
5. Add helpful comments and console output
6. Use AlgorandClient.defaultLocalNet() pattern

REFINEMENT PROCESS:
1. Analyze the issue description and severity
2. Locate the problem in the code
3. Apply the recommended fix
4. Ensure the fix doesn't break anything else
5. Return only the files that were modified (null for unchanged)

EXAMPLES OF FIXES:

Issue: "Code imports from 'algosdk' instead of '@algorandfoundation/algokit-utils'"
Fix: Replace algosdk imports with equivalent algokit-utils imports

Issue: "Missing environment variable INDEXER_SERVER in .env.example"
Fix: Add INDEXER_SERVER with example value to .env.example

Issue: "Code contains test scaffolding: expect("
Fix: Remove expect() and related test code, replace with console.log

Issue: "algokit-utils dependency should be 'file:../../dist'"
Fix: Update package.json to use correct dependency path

Be precise and surgical - only fix what's broken."""


async def refine_example(
    agent: Agent,
    example_id: str,
    issues: list[dict],
    current_main_code: str,
    current_readme: str,
    current_package_json: str,
    current_env_example: str | None,
) -> RefinedFiles:
    """Refine an example by fixing issues

    Args:
        agent: Configured pydantic-ai Agent
        example_id: Example identifier
        issues: List of issues to fix
        current_main_code: Current main.ts code
        current_readme: Current README.md
        current_package_json: Current package.json
        current_env_example: Current .env.example (if exists)

    Returns:
        RefinedFiles with fixed content
    """
    # Prepare issues description
    issues_text = "\n".join(
        [
            f"- [{issue['severity']}] {issue['description']}\n  Fix: {issue['recommendation']}"
            for issue in issues
        ]
    )

    # Prepare the prompt
    prompt = f"""Fix the following issues in this example.

Example ID: {example_id}

Issues to Fix:
{issues_text}

Current Files:

main.ts:
```typescript
{current_main_code}
```

README.md:
```markdown
{current_readme}
```

package.json:
```json
{current_package_json}
```

.env.example:
```
{current_env_example or "(not present)"}
```

Return:
- main_code: Fixed main.ts (or null if unchanged)
- readme_content: Fixed README.md (or null if unchanged)
- package_json: Fixed package.json (or null if unchanged)
- env_example: Fixed .env.example (or null if unchanged)
- notes: Brief description of changes made

Only return files that were actually modified. Set unchanged files to null."""

    # Run the agent
    print("      🤖 Running refinement agent...")
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


def refine_example_sync(
    agent: Agent,
    example_id: str,
    issues: list[dict],
    current_main_code: str,
    current_readme: str,
    current_package_json: str,
    current_env_example: str | None,
) -> RefinedFiles:
    """Synchronous version of refine_example"""
    import asyncio

    return asyncio.run(
        refine_example(
            agent,
            example_id,
            issues,
            current_main_code,
            current_readme,
            current_package_json,
            current_env_example,
        )
    )

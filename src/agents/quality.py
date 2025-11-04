"""Quality agent for validating generated examples"""

import time

from pydantic import BaseModel
from pydantic_ai import Agent

from ..models.workflow import LLMConfig

AGENT_RETRIES = 3
MODEL_MAX_TOKENS = 20000


class ValidationIssues(BaseModel):
    """Issues found during validation"""

    completeness_issues: list[str]
    api_usage_issues: list[str]
    artifact_issues: list[str]
    general_issues: list[str]


def create_quality_agent(llm_config: LLMConfig) -> Agent:
    """Create and configure the quality agent

    Args:
        llm_config: LLM configuration

    Returns:
        Configured pydantic-ai Agent
    """
    return Agent(
        llm_config.default_model,
        output_type=ValidationIssues,
        system_prompt=get_system_prompt(),
        retries=AGENT_RETRIES,
        model_settings={"max_tokens": MODEL_MAX_TOKENS},
    )


def get_system_prompt() -> str:
    """Get the system prompt for the quality agent"""
    return """You are an expert code reviewer specializing in example validation.

Your task is to analyze generated code examples and identify issues in these categories:

1. **Completeness Issues**: Missing files, incomplete documentation, missing prerequisites
2. **API Usage Issues**: Incorrect imports, using internal APIs, dependency mismatches
3. **Artifact Issues**: Missing artifacts, incorrect paths, non-functional artifacts
4. **General Issues**: Code quality, best practices, readability

CRITICAL RULES TO CHECK:
- Examples MUST only import from '@algorandfoundation/algokit-utils'
- Examples MUST NOT import from 'algosdk' (including types)
- package.json MUST use "file:../../dist" for algokit-utils
- package.json MUST have "type": "module"
- README MUST have clear setup and run instructions
- Code MUST have no test scaffolding (expect, assert, mock, spy)

For each issue found, provide:
- Clear description of the problem
- Specific location if applicable
- Recommended fix

Be thorough but focus on issues that prevent the example from running or being useful."""


async def validate_example(
    agent: Agent,
    example_id: str,
    main_code: str,
    package_json: str,
    readme_content: str,
    tsconfig_json: str,
) -> ValidationIssues:
    """Validate a generated example

    Args:
        agent: Configured pydantic-ai Agent
        example_id: Example identifier
        main_code: Main TypeScript code
        package_json: package.json content
        readme_content: README.md content
        tsconfig_json: tsconfig.json content

    Returns:
        ValidationIssues with found issues
    """
    # Prepare the prompt
    prompt = f"""Validate this generated example for quality issues.

Example ID: {example_id}

Main Code (main.ts):
```typescript
{main_code}
```

package.json:
```json
{package_json}
```

README.md:
```markdown
{readme_content}
```

tsconfig.json:
```json
{tsconfig_json}
```

Identify all issues in each category. Return empty lists for categories with no issues."""

    # Run the agent
    print("      🤖 Running quality validation agent...")
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


def validate_example_sync(
    agent: Agent,
    example_id: str,
    main_code: str,
    package_json: str,
    readme_content: str,
    tsconfig_json: str,
) -> ValidationIssues:
    """Synchronous version of validate_example"""
    import asyncio

    return asyncio.run(
        validate_example(agent, example_id, main_code, package_json, readme_content, tsconfig_json)
    )

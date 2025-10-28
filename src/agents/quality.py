"""Quality agent for validating generated examples"""

from pydantic import BaseModel
from pydantic_ai import Agent

from ..models.workflow import LLMConfig


class ValidationIssues(BaseModel):
    """Issues found during validation"""

    completeness_issues: list[str]
    api_usage_issues: list[str]
    artifact_issues: list[str]
    general_issues: list[str]


class QualityAgent:
    """Agent that validates generated examples for quality issues"""

    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config

        # Create the pydantic-ai agent
        self.agent = Agent(
            model=llm_config.default_model,
            result_type=ValidationIssues,
            system_prompt=self._get_system_prompt(),
        )

    def _get_system_prompt(self) -> str:
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
        self,
        example_id: str,
        main_code: str,
        package_json: str,
        readme_content: str,
        tsconfig_json: str,
    ) -> ValidationIssues:
        """Validate a generated example

        Args:
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
        result = await self.agent.run(prompt)

        return result.data

    def validate_example_sync(
        self,
        example_id: str,
        main_code: str,
        package_json: str,
        readme_content: str,
        tsconfig_json: str,
    ) -> ValidationIssues:
        """Synchronous version of validate_example"""
        import asyncio

        return asyncio.run(
            self.validate_example(
                example_id, main_code, package_json, readme_content, tsconfig_json
            )
        )


"""Distillation agent for planning example generation"""

from pydantic_ai import Agent

from ..models.phase_outputs import ExamplePlan
from ..models.workflow import LLMConfig


class DistillationAgent:
    """Agent that analyzes test blocks and plans example generation"""

    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config

        # Create the pydantic-ai agent
        self.agent = Agent(
            model=llm_config.default_model,
            result_type=list[ExamplePlan],
            system_prompt=self._get_system_prompt(),
        )

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the distillation agent"""
        return """You are an expert at planning code examples from test cases.

Your task is to analyze test blocks and create comprehensive plans for generating user-facing examples.

For each example plan:
1. Create a clear, descriptive title based on the use case
2. Write a concise summary of what the example demonstrates
3. Identify the target language (typescript, python, go, etc.)
4. Determine complexity (simple, moderate, complex)
5. List all features being demonstrated
6. Generate feature tags for categorization
7. Define folder path (examples/XX-kebab-case-title)
8. Specify prerequisites (tools, libraries, environment variables)
9. Define run instructions (setup, install, execute)
10. List expected output
11. Map to source test files
12. Plan artifacts (contracts, configs, data files)

Guidelines:
- Group related test blocks into single cohesive examples
- Prioritize high-value, user-facing features
- Keep examples focused and practical
- Ensure prerequisites are realistic and minimal
- Use clear, descriptive folder names
- Only use publicly available libraries
- Search thoroughly for existing artifacts before planning generation"""

    async def plan_examples(
        self,
        test_blocks: list[dict],
        repository_name: str,
    ) -> list[ExamplePlan]:
        """Plan example generation from test blocks

        Args:
            test_blocks: List of test blocks to analyze
            repository_name: Name of the repository

        Returns:
            List of ExamplePlan objects
        """
        # Prepare the prompt
        prompt = f"""Analyze these test blocks from the {repository_name} repository and create example plans:

Test Blocks:
```json
{test_blocks}
```

Create comprehensive plans for each example. Group related test blocks where appropriate.
Ensure each plan has complete metadata, prerequisites, and instructions."""

        # Run the agent
        result = await self.agent.run(prompt)

        return result.data

    def plan_examples_sync(
        self,
        test_blocks: list[dict],
        repository_name: str,
    ) -> list[ExamplePlan]:
        """Synchronous version of plan_examples"""
        import asyncio

        return asyncio.run(self.plan_examples(test_blocks, repository_name))

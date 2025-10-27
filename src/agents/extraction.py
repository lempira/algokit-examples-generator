"""Extraction agent for analyzing test files and extracting test blocks"""

from pydantic_ai import Agent

from ..models.phase_outputs import TestBlock, TestFileAnalysis
from ..models.workflow import LLMConfig


class ExtractionAgent:
    """Agent that analyzes test files and extracts test blocks with metadata"""

    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config

        # Create the pydantic-ai agent
        self.agent = Agent(
            model=llm_config.default_model,
            result_type=list[TestBlock],
            system_prompt=self._get_system_prompt(),
        )

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the extraction agent"""
        return """You are an expert code analyst specializing in test file analysis.

Your task is to analyze test files and extract individual test blocks with rich metadata.

For each test block, identify:
1. test_name: The name of the test function/block
2. line_range: Start and end line numbers (format: "start-end")
3. features_tested: List of specific features/APIs/methods being tested
4. feature_classification: "user-facing", "internal", or "mixed"
5. use_case_category: High-level category (only if user-facing/mixed)
6. specific_use_case: Concrete scenario (only if user-facing/mixed)
7. target_users: Array of user types (only if user-facing/mixed)
8. example_potential: "high", "medium", or "low"
9. complexity: "simple", "moderate", or "complex"
10. prerequisites: imports, setup_requirements, configuration
11. key_concepts: Main concepts demonstrated
12. user_value: Why this helps end users (only if user-facing/mixed)

Guidelines:
- Focus on extracting practical, valuable test blocks
- Identify user-facing features vs internal implementation details
- Be specific about use cases and target users
- Consider complexity and prerequisites realistically"""

    async def analyze_test_file(
        self,
        file_path: str,
        file_content: str,
        repository_name: str,
    ) -> TestFileAnalysis:
        """Analyze a test file and extract test blocks

        Args:
            file_path: Path to the test file
            file_content: Content of the test file
            repository_name: Name of the repository

        Returns:
            TestFileAnalysis with extracted test blocks
        """
        # Prepare the prompt
        prompt = f"""Analyze this test file from the {repository_name} repository:

File: {file_path}

```
{file_content}
```

Extract all test blocks and provide detailed metadata for each."""

        # Run the agent
        result = await self.agent.run(prompt)

        # Create and return the analysis
        return TestFileAnalysis(
            source_file=file_path,
            file_status="created",  # Will be updated by the node
            test_blocks=result.data,
        )

    def analyze_test_file_sync(
        self,
        file_path: str,
        file_content: str,
        repository_name: str,
    ) -> TestFileAnalysis:
        """Synchronous version of analyze_test_file"""
        import asyncio

        return asyncio.run(self.analyze_test_file(file_path, file_content, repository_name))

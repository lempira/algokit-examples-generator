"""Extraction agent for analyzing test files and extracting test blocks"""

import time

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from ..models import LLMConfig, TestBlock, TestFileAnalysis

AGENT_RETRIES = 3
MODEL_MAX_TOKENS = 20000


class TestBlockList(BaseModel):
    """Wrapper for list of test blocks (required for pydantic-ai)"""

    blocks: list[TestBlock] = Field(
        default_factory=list,
        description="Array of all test blocks found in the file. Return one TestBlock for each test() or it() call. Return empty array if no tests found.",
    )


def create_extraction_agent(llm_config: LLMConfig) -> Agent:
    """Create and configure the extraction agent

    Args:
        llm_config: LLM configuration

    Returns:
        Configured pydantic-ai Agent
    """
    return Agent(
        llm_config.default_model,
        output_type=TestBlockList,
        retries=AGENT_RETRIES,
        model_settings={"max_tokens": MODEL_MAX_TOKENS},
    )


def get_prompt_detailed_metadata(file_path: str, file_content: str, repository_name: str) -> str:
    """Original detailed prompt with 12 metadata fields and conditional logic"""
    return f"""You are an expert code analyst specializing in test file analysis.

        Your task is to analyze test files and extract individual test blocks with rich metadata.

        IMPORTANT: You must return a JSON array of test blocks. Even if you find no test blocks, return an empty array [].

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
        10. prerequisites: Object with imports, setup_requirements, configuration arrays
        11. key_concepts: Main concepts demonstrated
        12. user_value: Why this helps end users (only if user-facing/mixed)

        Guidelines:
        - Extract ALL test functions/blocks found in the file
        - For SDK/library tests, treat them as user-facing (developers are the users)
        - Provide your best assessment for each field - use defaults if uncertain
        - A test is valuable if it demonstrates how to use a feature or API
        - Always return an array, never an object or null

        ---

        Now analyze this test file from the {repository_name} repository:

        File: {file_path}

        ```
        {file_content}
        ```

        Extract all test blocks and provide detailed metadata for each.
    """


def get_prompt_simplified_direct(file_path: str, file_content: str, repository_name: str) -> str:
    """Simplified prompt with only 7 essential fields and direct instructions"""
    return f"""Analyze this test file and extract ALL test blocks (test functions/cases).

        For EACH test function, return an object with these fields:
        - test_name: The test function name (e.g., "test('Deploy new app', ...)" → "Deploy new app")
        - line_range: Approximate line numbers (e.g., "20-45")
        - features_tested: List main APIs/methods tested (e.g., ["appDeployer.deploy"])
        - feature_classification: Always use "user-facing" for SDK tests
        - example_potential: "high" if shows common use case, "medium" if specialized, "low" if edge case
        - complexity: "simple" if <20 lines, "moderate" if 20-50 lines, "complex" if >50 lines
        - key_concepts: Main concepts shown (e.g., ["app deployment", "metadata"])

        CRITICAL: Return a JSON array. If you find 10 tests, return 10 objects. Never return empty array unless file has zero tests.

        Test file from {repository_name}:

        {file_path}

        ```
        {file_content}
        ```

        Return array of ALL test blocks found.
    """


def get_prompt_minimal_count_first(file_path: str, file_content: str, repository_name: str) -> str:
    """Ultra-minimal prompt that asks LLM to count tests first"""
    return f"""Extract all test functions from this file.

        Step 1: Count how many test functions you see
        Step 2: For each test, provide:
        - test_name: the test name
        - features_tested: main APIs used
        - complexity: "simple", "moderate", or "complex"

        File: {file_path}

        ```
        {file_content}
        ```

        Return JSON array with one object per test function.
    """


def get_prompt_ultra_direct(file_path: str, file_content: str, repository_name: str) -> str:
    """Extremely direct prompt - just find tests and extract them"""
    return f"""Find every test case in this file and extract them.

EXAMPLES OF TEST PATTERNS TO LOOK FOR:
- test('test name', ...) or test("test name", ...)
- it('test name', ...) or it("test name", ...)
- describe.only, test.only, etc.

For EACH test you find, return ONE object with:
- test_name: the exact test name string
- line_range: approximate lines (e.g., "25-50")
- features_tested: list main APIs/methods (e.g., ["algorand.appDeployer.deploy", "algorand.send.appCreate"])
- complexity: "simple" if <30 lines, "moderate" if 30-60, "complex" if >60
- example_potential: "high" if shows common SDK usage, "medium" if specialized, "low" if edge case
- key_concepts: main topics (e.g., ["app deployment", "metadata", "error handling"])

CRITICAL: I can see there are multiple tests in this file. Return ALL of them as a JSON array.

File: {file_path}
Repository: {repository_name}

```
{file_content}
```

Return a JSON array. If you see 20 tests, return 20 objects. Do NOT return empty array.
    """


def get_prompt_schema_driven(file_path: str, file_content: str, repository_name: str) -> str:
    """Minimal prompt that relies on field descriptions in the schema"""
    return f"""Analyze this test file from the {repository_name} repository and extract all test cases.

File: {file_path}

```
{file_content}
```

TASK: Find every test() or it() call and extract comprehensive metadata for each one. Return ALL tests found - if you see 20 tests, return 20 objects.

The output schema describes exactly what information to extract for each field. Fill in as many fields as possible based on the test code.
"""


async def analyze_test_file(
    agent: Agent,
    file_path: str,
    file_content: str,
    repository_name: str,
) -> TestFileAnalysis:
    """Analyze a test file and extract test blocks

    Args:
        agent: Configured pydantic-ai Agent
        file_path: Path to the test file
        file_content: Content of the test file
        repository_name: Name of the repository

    Returns:
        TestFileAnalysis with extracted test blocks
    """
    # Choose which prompt to use (change this to test different prompts)
    # Options: get_prompt_detailed_metadata, get_prompt_simplified_direct, get_prompt_minimal_count_first, get_prompt_ultra_direct, get_prompt_schema_driven
    prompt = get_prompt_schema_driven(file_path, file_content, repository_name)

    # Run the agent with error handling and timing
    try:
        start_time = time.time()
        result = await agent.run(prompt)
        elapsed_time = time.time() - start_time

        print(f"    [{file_path}] Agent completed in {elapsed_time:.2f}s")
        print(f"    [{file_path}] Output length: {len(result.output.blocks)}")

        # Debug: Show first block if any
        if len(result.output.blocks) > 0:
            print(f"    [{file_path}] First block test_name: {result.output.blocks[0].test_name}")
        else:
            print(f"    [{file_path}] ⚠️  WARNING: Agent returned empty array!")

        # Create and return the analysis
        return TestFileAnalysis(
            source_file=file_path,
            test_blocks=result.output.blocks,
        )
    except Exception as e:
        # Log detailed error information for debugging
        print(f"\n=== DEBUG: Extraction failed for {file_path} ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")

        # Try to extract more details from pydantic-ai errors
        if hasattr(e, "__cause__") and e.__cause__:
            print(f"Caused by: {e.__cause__}")

        if hasattr(e, "messages"):
            print(f"Messages: {e.messages}")

        # Re-raise the error after logging
        raise


# def analyze_test_file_sync(
#     agent: Agent,
#     file_path: str,
#     file_content: str,
#     repository_name: str,
# ) -> TestFileAnalysis:
#     """Synchronous version of analyze_test_file

#     Args:
#         agent: Configured pydantic-ai Agent
#         file_path: Path to the test file
#         file_content: Content of the test file
#         repository_name: Name of the repository

#     Returns:
#         TestFileAnalysis with extracted test blocks
#     """
#     import asyncio

#     return asyncio.run(analyze_test_file(agent, file_path, file_content, repository_name))

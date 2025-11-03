#!/usr/bin/env python3
"""
Run individual workflow phases with sample data.

Usage:
    # Run extraction phase
    uv run python scripts/run_phase.py extraction --repo /path/to/repo

    # Run distillation phase
    uv run python scripts/run_phase.py distillation

    # Run with custom input/output directories
    uv run python scripts/run_phase.py generation --repo /path/to/repo \
        --input-dir my-inputs --output-dir my-outputs

    # Run with specific model
    uv run python scripts/run_phase.py extraction --repo /path/to/repo \
        --model claude-3-5-sonnet-latest
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.models import LLMConfig
from src.nodes.discovery import DiscoveryNode
from src.nodes.distillation import DistillationNode
from src.nodes.extraction import ExtractionNode
from src.nodes.generation import GenerationNode
from src.nodes.quality import QualityNode
from src.nodes.refinement import RefinementNode
from src.utils.code_executor import CodeExecutor
from src.utils.file_reader import CodeFileReader
from src.utils.json_store import JSONStore


def run_discovery(args):
    """Run Phase 1: Discovery"""
    print("=" * 60)
    print("Running Phase 1: Discovery")
    print("=" * 60)

    repo_path = Path(args.repo).resolve()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_store = JSONStore(output_dir)

    print(f"Repository: {repo_path}")
    print(f"Output: {output_dir / '01-discovery.json'}")

    if args.discovery_files:
        print(f"\nProcessing only {len(args.discovery_files)} specific files:")
        for f in args.discovery_files:
            print(f"  - {f}")

    node = DiscoveryNode(
        repo_path=repo_path,
        json_store=json_store,
        discovery_paths=settings.get_discovery_paths(),
        filter_files=args.discovery_files,
    )

    result = node.run(args.repository_name)

    print(f"\n✓ Found {result.summary.total_files} test files")
    print(f"  Output saved to: {output_dir / '01-discovery.json'}")


def run_extraction(args):
    """Run Phase 2: Extraction"""
    print("=" * 60)
    print("Running Phase 2: Extraction")
    print("=" * 60)

    repo_path = Path(args.repo).resolve()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check for required input
    discovery_file = input_dir / "01-discovery.json"
    if not discovery_file.exists():
        print(f"✗ Error: Required input file not found: {discovery_file}", file=sys.stderr)
        print("  Run discovery phase first or create sample input.", file=sys.stderr)
        sys.exit(1)

    json_store = JSONStore(output_dir)
    file_reader = CodeFileReader(repo_path)
    llm_config = LLMConfig(
        default_model=args.model or settings.default_model,
        temperature=settings.temperature,
    )

    # Copy discovery file to output dir for node to read
    import shutil

    from src.models import DiscoveryResult

    shutil.copy(discovery_file, output_dir / "01-discovery.json")

    # Filter discovery results if specific files are requested
    if args.extraction_files:
        print(f"Filtering to {len(args.extraction_files)} specific files:")
        for f in args.extraction_files:
            print(f"  - {f}")

        # Load discovery results and filter
        discovery_data = json_store.read_sync("01-discovery.json")
        discovery_result = DiscoveryResult.model_validate(discovery_data)
        original_count = len(discovery_result.test_files)

        # Filter to only the requested files
        filtered_files = [
            tf for tf in discovery_result.test_files if tf.path in args.extraction_files
        ]

        if len(filtered_files) == 0:
            print(
                "\n✗ Error: None of the specified files were found in discovery results",
                file=sys.stderr,
            )
            print(
                f"  Available files: {[tf.path for tf in discovery_result.test_files[:5]]}",
                file=sys.stderr,
            )
            sys.exit(1)

        # Update discovery result with filtered files
        discovery_result.test_files = filtered_files
        discovery_result.summary.total_files = len(filtered_files)

        # Save filtered discovery
        json_store.write_sync("01-discovery.json", discovery_result)
        print(f"  Filtered from {original_count} to {len(filtered_files)} files\n")

    print(f"Repository: {repo_path}")
    print(f"Input: {discovery_file}")
    print(f"Output: {output_dir / '02-extraction.json'}")
    print(f"Model: {llm_config.default_model}")

    node = ExtractionNode(
        repo_path=repo_path,
        json_store=json_store,
        file_reader=file_reader,
        llm_config=llm_config,
    )

    result = node.run(args.repository_name)

    print(f"\n✓ Extracted {result.summary.total_test_blocks} test blocks")
    print(f"  Output saved to: {output_dir / '02-extraction.json'}")


def run_distillation(args):
    """Run Phase 3: Distillation"""
    print("=" * 60)
    print("Running Phase 3: Distillation")
    print("=" * 60)

    repo_path = Path(args.repo).resolve() if args.repo else Path.cwd()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check for required input
    extraction_file = input_dir / "02-extraction.json"
    if not extraction_file.exists():
        print(f"✗ Error: Required input file not found: {extraction_file}", file=sys.stderr)
        print("  Run extraction phase first or create sample input.", file=sys.stderr)
        sys.exit(1)

    json_store = JSONStore(output_dir)
    llm_config = LLMConfig(
        default_model=args.model or settings.default_model,
        temperature=settings.temperature,
    )

    # Copy extraction file to output dir for node to read
    import shutil

    shutil.copy(extraction_file, output_dir / "02-extraction.json")

    print(f"Repository: {repo_path}")
    print(f"Input: {extraction_file}")
    print(f"Output: {output_dir / '03-distillation.json'}")
    print(f"Model: {llm_config.default_model}")

    node = DistillationNode(
        repo_path=repo_path,
        json_store=json_store,
        llm_config=llm_config,
    )

    result = node.run(args.repository_name)

    print(f"\n✓ Planned {result.summary.total_examples} examples")
    print(f"  Output saved to: {output_dir / '03-distillation.json'}")


def run_generation(args):
    """Run Phase 4: Generation"""
    print("=" * 60)
    print("Running Phase 4: Generation")
    print("=" * 60)

    repo_path = Path(args.repo).resolve()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check for required input
    distillation_file = input_dir / "03-distillation.json"
    if not distillation_file.exists():
        print(f"✗ Error: Required input file not found: {distillation_file}", file=sys.stderr)
        print("  Run distillation phase first or create sample input.", file=sys.stderr)
        sys.exit(1)

    json_store = JSONStore(output_dir)
    file_reader = CodeFileReader(repo_path)
    llm_config = LLMConfig(
        default_model=args.model or settings.default_model,
        temperature=settings.temperature,
    )

    # Copy distillation file to output dir for node to read
    import shutil

    shutil.copy(distillation_file, output_dir / "03-distillation.json")

    print(f"Repository: {repo_path}")
    print(f"Input: {distillation_file}")
    print(f"Output: {output_dir / '04-generation.json'}")
    print(f"Examples output: {output_dir}")
    print(f"Model: {llm_config.default_model}")

    node = GenerationNode(
        repo_path=repo_path,
        examples_path=output_dir,
        json_store=json_store,
        file_reader=file_reader,
        llm_config=llm_config,
    )

    result = node.run(args.repository_name)

    print(f"\n✓ Generated {result.summary.generated} examples")
    print(f"  Output saved to: {output_dir / '04-generation.json'}")


def run_quality(args):
    """Run Phase 5: Quality"""
    print("=" * 60)
    print("Running Phase 5: Quality")
    print("=" * 60)

    repo_path = Path(args.repo).resolve() if args.repo else Path.cwd()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check for required input
    generation_file = input_dir / "04-generation.json"
    if not generation_file.exists():
        print(f"✗ Error: Required input file not found: {generation_file}", file=sys.stderr)
        print("  Run generation phase first or create sample input.", file=sys.stderr)
        sys.exit(1)

    json_store = JSONStore(output_dir)
    executor = CodeExecutor()
    llm_config = LLMConfig(
        default_model=args.model or settings.default_model,
        temperature=settings.temperature,
    )

    # Copy generation file to output dir for node to read
    import shutil

    shutil.copy(generation_file, output_dir / "04-generation.json")

    print(f"Repository: {repo_path}")
    print(f"Input: {generation_file}")
    print(f"Output: {output_dir / '05-quality.json'}")
    print(f"Model: {llm_config.default_model}")

    node = QualityNode(
        repo_path=repo_path,
        examples_path=output_dir,
        json_store=json_store,
        executor=executor,
        llm_config=llm_config,
        iteration=1,
    )

    result = node.run(args.repository_name)

    print(f"\n✓ Validated {result.validation_results.examples_validated} examples")
    print(f"  Total issues: {result.severity_summary.total}")
    print(f"  Output saved to: {output_dir / '05-quality.json'}")


def run_refinement(args):
    """Run Phase 6: Refinement"""
    print("=" * 60)
    print("Running Phase 6: Refinement")
    print("=" * 60)

    repo_path = Path(args.repo).resolve() if args.repo else Path.cwd()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check for required input
    quality_file = input_dir / "05-quality.json"
    if not quality_file.exists():
        print(f"✗ Error: Required input file not found: {quality_file}", file=sys.stderr)
        print("  Run quality phase first or create sample input.", file=sys.stderr)
        sys.exit(1)

    json_store = JSONStore(output_dir)
    llm_config = LLMConfig(
        default_model=args.model or settings.default_model,
        temperature=settings.temperature,
    )

    # Copy quality and generation files to output dir for node to read
    import shutil

    shutil.copy(quality_file, output_dir / "05-quality.json")
    generation_file = input_dir / "04-generation.json"
    if generation_file.exists():
        shutil.copy(generation_file, output_dir / "04-generation.json")

    print(f"Repository: {repo_path}")
    print(f"Input: {quality_file}")
    print(f"Output: {output_dir / '06-refinement.json'}")
    print(f"Model: {llm_config.default_model}")

    node = RefinementNode(
        repo_path=repo_path,
        examples_path=output_dir,
        json_store=json_store,
        llm_config=llm_config,
        iteration=1,
    )

    result = node.run(args.repository_name)

    print(f"\n✓ Applied {result.changes_applied} fixes")
    print(f"  Updated {len(result.examples_updated)} examples")
    print(f"  Output saved to: {output_dir / '06-refinement.json'}")


def main():
    parser = argparse.ArgumentParser(
        description="Run individual workflow phases with sample data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run discovery
  python scripts/run_phase.py discovery --repo /path/to/repo

  # Run extraction (requires 01-discovery.json)
  python scripts/run_phase.py extraction --repo /path/to/repo

  # Run distillation (requires 02-extraction.json)
  python scripts/run_phase.py distillation

  # Use custom directories
  python scripts/run_phase.py extraction --repo /path/to/repo \\
      --input-dir my-inputs --output-dir my-outputs
        """,
    )

    parser.add_argument(
        "phase",
        choices=["discovery", "extraction", "distillation", "generation", "quality", "refinement"],
        help="Phase to run",
    )

    parser.add_argument(
        "--repo",
        type=str,
        help="Path to the repository (required for discovery, extraction, generation)",
    )

    parser.add_argument(
        "--repository-name",
        type=str,
        default="test-repo",
        help="Name of the repository (default: test-repo)",
    )

    parser.add_argument(
        "--input-dir",
        type=str,
        default="dev-inputs",
        help="Directory containing input JSON files (default: dev-inputs)",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="dev-outputs",
        help="Directory for output JSON files (default: dev-outputs)",
    )

    parser.add_argument(
        "--model",
        type=str,
        help="LLM model to use (default: from config)",
    )

    parser.add_argument(
        "--discovery-files",
        type=str,
        nargs="+",
        help="Specific files to process (discovery phase only)",
    )

    parser.add_argument(
        "--extraction-files",
        type=str,
        nargs="+",
        help="Specific files to process (extraction phase only)",
    )

    args = parser.parse_args()

    # Validate required arguments
    if args.phase in ["discovery", "extraction", "generation"] and not args.repo:
        parser.error(f"{args.phase} phase requires --repo argument")

    # Run the appropriate phase
    try:
        if args.phase == "discovery":
            run_discovery(args)
        elif args.phase == "extraction":
            run_extraction(args)
        elif args.phase == "distillation":
            run_distillation(args)
        elif args.phase == "generation":
            run_generation(args)
        elif args.phase == "quality":
            run_quality(args)
        elif args.phase == "refinement":
            run_refinement(args)
    except Exception as e:
        print(f"\n✗ Error running {args.phase} phase:", file=sys.stderr)
        print(f"  {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

"""CLI interface for algokit-examples-generator"""

import argparse
import sys
from pathlib import Path

from . import __version__
from .config import settings
from .workflow import create_workflow


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="algokit-examples-gen",
        description="AI-powered system to convert test files into runnable user-facing examples",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate examples from current directory
  algokit-examples-gen

  # Generate examples from specific repository
  algokit-examples-gen /path/to/repo

  # Use specific LLM model
  algokit-examples-gen --model anthropic:claude-3-5-sonnet-20241022

  # Specify custom output directory
  algokit-examples-gen --output ./my-examples

For more information, visit: https://github.com/algorandfoundation/algokit-examples-generator
        """,
    )

    parser.add_argument(
        "repo_path",
        nargs="?",
        default=".",
        help="Path to the repository (default: current directory)",
    )

    parser.add_argument(
        "-o",
        "--output",
        dest="output_path",
        help="Output directory for examples (default: <repo>/examples)",
    )

    parser.add_argument(
        "-m",
        "--model",
        dest="model",
        help=f"LLM model to use (default: {settings.default_model})",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Resolve paths - CLI args override config
    # repo_path: use CLI arg if provided, otherwise use config
    repo_path = (
        Path(args.repo_path).resolve() if args.repo_path != "." else settings.get_repo_path()
    )

    if not repo_path.exists():
        print(f"Error: Repository path does not exist: {repo_path}", file=sys.stderr)
        sys.exit(1)

    if not repo_path.is_dir():
        print(f"Error: Repository path is not a directory: {repo_path}", file=sys.stderr)
        sys.exit(1)

    # output_path: use CLI arg if provided, otherwise use config, otherwise default to <repo>/examples
    if args.output_path:
        output_path = Path(args.output_path).resolve()
    elif settings.get_examples_output_path() is not None:
        output_path = settings.get_examples_output_path()
    else:
        output_path = repo_path / "examples"

    # model: use CLI arg if provided, otherwise use config
    model = args.model if args.model else settings.default_model

    # Derive repository name from path
    repository_name = repo_path.name

    # Display configuration
    print(f"AlgoKit Examples Generator v{__version__}")
    print("=" * 60)
    print(f"Repository: {repository_name}")
    print(f"Path: {repo_path}")
    print(f"Output: {output_path}")
    print(f"Model: {model}")
    print(f"Temperature: {settings.temperature}")
    print(f"Max Refinement Iterations: {settings.max_refinement_iterations}")
    print("=" * 60)
    print()

    try:
        # Create and run workflow
        workflow = create_workflow(
            repo_path=repo_path,
            examples_output_path=output_path,
            llm_model=model,
            temperature=settings.temperature,
            max_refinement_iterations=settings.max_refinement_iterations,
        )

        workflow.run(repository_name)

        print("\n✓ Examples generated successfully!")
        print(f"  Output location: {workflow.deps.examples_output_path}")

        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n⚠ Workflow interrupted by user", file=sys.stderr)
        sys.exit(130)

    except Exception as e:
        print(f"\n\n✗ Error: {e}", file=sys.stderr)

        if args.verbose:
            import traceback

            print("\nFull traceback:", file=sys.stderr)
            traceback.print_exc()

        sys.exit(1)


if __name__ == "__main__":
    main()

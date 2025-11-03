"""Main entry point for the algokit-examples-generator

This module re-exports the CLI for backwards compatibility.
Use `algokit-examples-gen` command or `python -m src.cli` instead.
"""

from .cli import main

__all__ = ["main"]


if __name__ == "__main__":
    main()

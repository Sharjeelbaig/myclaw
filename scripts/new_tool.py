#!/usr/bin/env python3
"""Scaffold a new standalone tool for the Deep Agent.

Usage:
    # Interactive:
    uv run python scripts/new_tool.py

    # CLI:
    uv run python scripts/new_tool.py --name webSearch --description "Searches the web for documentation"
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "src" / "tools"

IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def camel_to_snake(name: str) -> str:
    """webSearch -> web_search"""
    step1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    step2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", step1)
    return step2.lower()


def tool_source(tool_name: str, description: str) -> str:
    return f'''from langchain.tools import tool


@tool
def {tool_name}(query: str) -> str:
    """{description}"""
    # TODO: Implement tool functionality here
    return f"Result for {{query}}"
'''


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold a new tool in src/tools/")
    parser.add_argument("--name", help="Tool function name in camelCase (e.g. webSearch)")
    parser.add_argument("--description", help="Description of what the tool does")

    args = parser.parse_args()

    if args.name:
        tool_name = args.name.strip()
        description = args.description or f"Executes {tool_name} operation."
    else:
        print("== New Tool ==\n")
        while True:
            tool_name = input("Tool name (camelCase, e.g. webSearch): ").strip()
            if not IDENT_RE.match(tool_name):
                print("  ! Invalid python identifier name")
                continue
            break
        description = input("Description: ").strip() or f"Executes {tool_name} operation."

    file_name = f"{camel_to_snake(tool_name)}.py"
    target_path = TOOLS_DIR / file_name

    if target_path.exists():
        print(f"Error: {target_path} already exists.", file=sys.stderr)
        return 1

    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    target_path.write_text(tool_source(tool_name, description))

    print(f"\nCreated {target_path.relative_to(ROOT)}")
    print("\nNext steps:")
    print(f"  1. Implement logic in src/tools/{file_name}")
    print(f"  2. Import into src/main.py: from tools.{camel_to_snake(tool_name)} import {tool_name}")
    print("  3. Add to tools list in create_deep_agent(tools=[..., {tool_name}])")
    return 0


if __name__ == "__main__":
    sys.exit(main())

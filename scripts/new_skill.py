#!/usr/bin/env python3
"""Scaffold a new progressive-disclosure Skill in .agents/skills/.

Usage:
    # Interactive:
    uv run python scripts/new_skill.py

    # CLI:
    uv run python scripts/new_skill.py --name git-workflows --description "Best practices for branching and commit conventions"
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / ".agents" / "skills"

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def skill_content(name: str, description: str) -> str:
    title = name.replace("-", " ").replace("_", " ").title()
    return f"""---
name: {name}
description: "{description}"
---

# {title} Skill

## Overview
Brief explanation of when and why the agent should consult this skill.

## When to Use
- Condition 1: When user requests ...
- Condition 2: When encountering ...

## Instructions
1. Step-by-step guidance for the agent.
2. Best practices and rules.

## Examples
Provide clear, actionable code snippets or interaction examples.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold a new skill in .agents/skills/")
    parser.add_argument("--name", help="Skill directory name in kebab-case (e.g. git-workflows)")
    parser.add_argument("--description", help="Description for YAML frontmatter")

    args = parser.parse_args()

    if args.name:
        name = args.name.strip().lower()
        description = (args.description or "").strip()
        if not description:
            print("Error: --description is required", file=sys.stderr)
            return 1
    else:
        print("== New Skill ==\n")
        while True:
            name = input("Skill name (kebab-case, e.g. git-workflows): ").strip().lower()
            if not NAME_RE.match(name):
                print("  ! Use lowercase letters, digits, dashes or underscores")
                continue
            break
        while True:
            description = input("Skill description: ").strip()
            if description:
                break
            print("  ! Description is required")

    skill_dir = SKILLS_DIR / name
    if skill_dir.exists():
        print(f"Error: {skill_dir} already exists.", file=sys.stderr)
        return 1

    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(skill_content(name, description))

    print(f"\nCreated {skill_file.relative_to(ROOT)}")
    print(f"\nSkill '{name}' is automatically discoverable by Deep Agents SkillsMiddleware.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

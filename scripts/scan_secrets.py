#!/usr/bin/env python3
"""
Pre-commit / CI Secret Scanner for TechFit Agent.
Scans tracked files and staged changes to ensure no sensitive API keys,
passwords, or live environment variables leak into version control.
"""

import os
import re
import sys
from pathlib import Path

# Patterns indicating potential secrets
SECRET_PATTERNS = [
    (r"(?i)(AIza[0-9A-Za-z-_]{35})", "Google / Gemini API Key"),
    (r"(?i)(ghp_[0-9a-zA-Z]{36})", "GitHub Personal Access Token"),
    (r"(?i)(sk-[0-9a-zA-Z]{32,})", "OpenAI / Generic Secret Key"),
    (r"(?i)(postgres://[a-zA-Z0-9_-]+:[^@\s]+@)", "Postgres URI with password"),
    (r"(?i)(postgresql://[a-zA-Z0-9_-]+:[^@\s]+@)", "Postgres URI with password"),
    (r"(?i)(GEMINI_API_KEY\s*=\s*['\"][0-9a-zA-Z-_]{20,}['\"])", "Hardcoded GEMINI_API_KEY"),
    (r"(?i)(SEARCH_API_KEY\s*=\s*['\"][0-9a-zA-Z-_]{20,}['\"])", "Hardcoded SEARCH_API_KEY"),
    (r"(?i)(PRODUCT_DETAILS_API_KEY\s*=\s*['\"][0-9a-zA-Z-_]{20,}['\"])", "Hardcoded PRODUCT_DETAILS_API_KEY"),
]

# Files/folders to ignore during secret scan
IGNORED_PATHS = {
    ".git",
    "node_modules",
    ".pytest_cache",
    "dist",
    "build",
    "__pycache__",
    ".env.example",
    "scan_secrets.py",
}

def scan_file(filepath: Path) -> list[str]:
    findings = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return [f"Could not read {filepath}: {e}"]

    for pattern, description in SECRET_PATTERNS:
        matches = re.finditer(pattern, content)
        for match in matches:
            # Check for dummy placeholder markers
            matched_str = match.group(0)
            if "your_" in matched_str.lower() or "example" in matched_str.lower() or "dummy" in matched_str.lower():
                continue
            findings.append(f"Line {content[:match.start()].count(chr(10)) + 1}: Found potential {description}")
    return findings

def main() -> int:
    root_dir = Path(__file__).resolve().parent.parent
    violations = {}

    for path in root_dir.rglob("*"):
        if path.is_file():
            # Skip ignored paths
            if any(part in IGNORED_PATHS for part in path.parts):
                continue
            # Specifically forbid committing .env or any .env.* except .env.example
            if path.name.startswith(".env") and path.name != ".env.example":
                violations[str(path)] = ["CRITICAL: .env file detected! It must never be committed to git."]
                continue

            findings = scan_file(path)
            if findings:
                violations[str(path.relative_to(root_dir))] = findings

    if violations:
        print("\n[FAILED] Secret Scanner detected potential secret leaks:")
        for file, issues in violations.items():
            print(f"  File: {file}")
            for issue in issues:
                print(f"    - {issue}")
        print("\nPlease remove these secrets or add them to .gitignore before committing.\n")
        return 1

    print("[PASSED] Secret scan clean. No leaked credentials detected.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

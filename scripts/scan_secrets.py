#!/usr/bin/env python3
"""
Pre-commit / CI Secret Scanner for TechFit Agent.
Scans tracked files and staged changes to ensure no sensitive API keys,
passwords, or live environment variables leak into version control.
"""

import os
import re
import sys
import subprocess
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

def is_env_tracked() -> bool:
    """Check if .env is tracked in git (which would be a violation)."""
    try:
        res = subprocess.run(
            ["git", "ls-files", ".env"],
            capture_output=True,
            text=True,
            check=False
        )
        return bool(res.stdout.strip())
    except Exception:
        return False

def scan_file(filepath: Path) -> list[str]:
    findings = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return [f"Could not read {filepath}: {e}"]

    for pattern, description in SECRET_PATTERNS:
        matches = re.finditer(pattern, content)
        for match in matches:
            matched_str = match.group(0)
            if "your_" in matched_str.lower() or "example" in matched_str.lower() or "dummy" in matched_str.lower():
                continue
            findings.append(f"Line {content[:match.start()].count(chr(10)) + 1}: Found potential {description}")
    return findings

def main() -> int:
    root_dir = Path(__file__).resolve().parent.parent
    violations = {}

    # Critical check: is .env accidentally tracked in git?
    if is_env_tracked():
        violations[".env"] = ["CRITICAL: .env file is tracked in git! It must be removed from git tracking."]

    for path in root_dir.rglob("*"):
        if path.is_file():
            # Skip ignored paths and local gitignored .env files
            if any(part in IGNORED_PATHS for part in path.parts):
                continue
            if path.name.startswith(".env") and path.name != ".env.example":
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
        print("\nPlease remove these secrets before committing.\n")
        return 1

    print("[PASSED] Secret scan clean. No leaked credentials detected.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

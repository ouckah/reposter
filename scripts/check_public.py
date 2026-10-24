"""Fail closed on unapproved release files; report locations, never matched values."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORED_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache"}
PATTERNS = {
    "provider credential": re.compile(
        r"gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|"
        r"sk-(?:ant|proj)-[A-Za-z0-9_-]{25,}|AIza[A-Za-z0-9_-]{30,}|"
        r"xox[baprs]-[A-Za-z0-9-]{20,}|AKIA[A-Z0-9]{16}|1//[A-Za-z0-9_-]{30,}"
    ),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "webhook credential": re.compile(r"https://hooks[.]slack[.]com/services/\w+/\w+/\w+"),
    "local user path": re.compile(r"/(?:Users|home)/[A-Za-z0-9._-]+/"),
    "private production reference": re.compile(r"ouckah" + r"-llc/"),
}
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def check(root: Path) -> list[str]:
    problems: list[str] = []
    manifest = root / "release-files.txt"
    if manifest.is_symlink() or not manifest.is_file():
        return ["Missing or symlinked release manifest"]
    entries = manifest.read_text().splitlines()
    expected = {line for line in entries if line and not line.startswith("#")}
    for name in expected:
        path = Path(name)
        if path.is_absolute() or ".." in path.parts:
            problems.append("Unsafe manifest path")
    if problems:
        return problems

    def walk(directory: Path):
        for path in sorted(directory.iterdir()):
            if path.is_symlink():
                problems.append(f"Symlink not permitted: {path.relative_to(root)}")
            elif path.is_dir():
                if path.name not in IGNORED_DIRS and not path.name.endswith(".egg-info"):
                    yield from walk(path)
            else:
                yield path

    actual = {str(path.relative_to(root)) for path in walk(root)}
    problems.extend(f"Unapproved file: {name}" for name in sorted(actual - expected))
    problems.extend(f"Missing release file: {name}" for name in sorted(expected - actual))

    # Ignored local build caches must never sneak into a commit.
    if (root / ".git").exists():
        result = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True)
        if result.returncode:
            problems.append("Unable to inspect tracked paths")
        else:
            tracked = set(result.stdout.decode().strip("\0").split("\0")) - {""}
            problems.extend(f"Unapproved tracked file: {name}" for name in sorted(tracked - expected))

    for name in sorted(expected & actual):
        path = root / name
        if path.stat().st_size > 1_000_000:
            problems.append(f"Oversized file: {name}")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeError:
            problems.append(f"Binary file: {name}")
            continue
        for number, line in enumerate(content.splitlines(), 1):
            for label, pattern in PATTERNS.items():
                if pattern.search(line):
                    problems.append(f"{name}:{number}: {label}")
            if any(email != "ouckah@gmail.com" for email in EMAIL.findall(line)):
                problems.append(f"{name}:{number}: unapproved email")
            if (name == ".env.example" and "=" in line
                    and not line.lstrip().startswith("#") and line.partition("=")[2].strip()):
                problems.append(f"{name}:{number}: populated credential template")
    return problems


if __name__ == "__main__":
    issues = check(ROOT)
    for issue in issues:
        print(issue, file=sys.stderr)
    if issues:
        raise SystemExit(1)
    print("Release allowlist and limited privacy-pattern checks passed. "
          "Run Gitleaks and manual review separately.")

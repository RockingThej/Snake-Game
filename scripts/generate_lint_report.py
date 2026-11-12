"""Generate Lint summary matching the project's CI pipeline specification.

Calculates:
- Statements via Python AST
- Blocking errors (E9, F63, F7, F82)
- Code warnings (Pyflakes F-series)
- Lint score via Pylint formula: 10 - ((5 * blocking + warnings) / statements) * 10
- Files with no warnings percentage
- Most frequent warnings breakdown
Outputs GitHub Step Summary and GITHUB_OUTPUT variables.
"""
import ast
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

EXCLUDED_DIRS = {".venv", "venv", ".git", "__pycache__", ".pytest_cache", "build", "dist", "instance"}


def get_python_files(repo_root: Path):
    py_files = []
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for f in files:
            if f.endswith(".py"):
                py_files.append(Path(root) / f)
    return sorted(py_files)


def count_statements(py_files):
    total = 0
    for file_path in py_files:
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))
            total += sum(isinstance(node, ast.stmt) for node in ast.walk(tree))
        except Exception:
            pass
    return max(1, total)


def run_flake8(repo_root: Path, select_codes: str):
    cmd = [
        sys.executable,
        "-m",
        "flake8",
        f"--select={select_codes}",
        "--exclude=" + ",".join(sorted(EXCLUDED_DIRS)),
        ".",
    ]
    res = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
    return lines


def parse_issues(lines):
    # Pattern: filename:line:col: CODE description
    pattern = re.compile(r"^([^:]+):(\d+):(\d+):\s*([A-Z]\d+)\s+(.*)$")
    issues = []
    for line in lines:
        m = pattern.match(line)
        if m:
            file_path, line_no, col, code, desc = m.groups()
            issues.append({
                "file": os.path.normpath(file_path),
                "line": int(line_no),
                "col": int(col),
                "code": code,
                "desc": desc,
            })
    return issues


def main():
    repo_root = Path(__file__).resolve().parent.parent
    py_files = get_python_files(repo_root)
    total_files = len(py_files)
    total_statements = count_statements(py_files)

    # 1. Blocking errors: syntax errors, undefined names
    blocking_lines = run_flake8(repo_root, "E9,F63,F7,F82")
    blocking_issues = parse_issues(blocking_lines)
    blocking_count = len(blocking_issues)

    # 2. Pyflakes code warnings (unused imports, unused vars, redefinitions, etc.)
    warning_lines = run_flake8(repo_root, "F401,F811,F841,F402,F403,F404,F405,F504,F522,F523,F541,F601,F602,F824,F842")
    warning_issues = parse_issues(warning_lines)
    warning_count = len(warning_issues)

    # Pylint formula: 10 - ((5 * fatal/error + warning) / statements) * 10
    deduction = ((5.0 * blocking_count + warning_count) / float(total_statements)) * 10.0
    score = max(0.0, min(10.0, 10.0 - deduction))

    # Warning-free files count
    files_with_warnings = {issue["file"] for issue in (blocking_issues + warning_issues)}
    clean_files_count = total_files - len(files_with_warnings)
    clean_files_pct = (clean_files_count / total_files * 100.0) if total_files > 0 else 100.0

    # Most frequent warnings
    warning_code_counts = Counter(issue["code"] for issue in warning_issues)
    if warning_code_counts:
        freq_str = ", ".join(f"`{code}` ×{count}" for code, count in warning_code_counts.most_common(5))
    else:
        freq_str = "None"

    blocking_badge = f"{blocking_count} · ✅ Pass" if blocking_count == 0 else f"{blocking_count} · ❌ Fail"

    summary_md = f"""## 1 · Lint summary

### 1 · Lint

| Check | Result |
|---|---|
| Lint score (pylint formula) | **{score:.2f} / 10** |
| Python files / statements checked | {total_files} / {total_statements} |
| Blocking errors (syntax, undefined names) | {blocking_badge} |
| Code warnings (pyflakes: unused imports and variables, non-blocking) | {warning_count} |
| Files with no warnings | {clean_files_count}/{total_files} ({clean_files_pct:.1f}%) |
| Most frequent warnings | {freq_str} |

<sub>Job summary generated at run-time</sub>
"""

    print(summary_md)

    # Write to GITHUB_STEP_SUMMARY if available
    step_summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary_file:
        with open(step_summary_file, "a", encoding="utf-8") as f:
            f.write(summary_md + "\n")

    # Output to GITHUB_OUTPUT if available
    github_output_file = os.environ.get("GITHUB_OUTPUT")
    score_str = f"{score:.2f}"
    summary_line = f"{score_str} / 10 · {blocking_count} blocking errors · {clean_files_pct:.1f}% files warning-free ({warning_count} code warnings)"
    if github_output_file:
        with open(github_output_file, "a", encoding="utf-8") as f:
            f.write(f"score={score_str}\n")
            f.write(f"total_files={total_files}\n")
            f.write(f"total_statements={total_statements}\n")
            f.write(f"blocking_errors={blocking_count}\n")
            f.write(f"warning_count={warning_count}\n")
            f.write(f"clean_files_pct={clean_files_pct:.1f}%\n")
            f.write(f"summary_line={summary_line}\n")
            f.write(f"status={'success' if blocking_count == 0 else 'failure'}\n")

    if blocking_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

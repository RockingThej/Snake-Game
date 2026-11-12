"""Run pytest with coverage and generate the test & coverage summary report.

Matches the CI scorecard specification:
- Tests run, passed, failed, errors, skipped
- Pass rate
- Duration
- Statement coverage
- Branch coverage
- Combined coverage (gate >= 80%)
- Collapsible Coverage per file table
Outputs GitHub Step Summary and GITHUB_OUTPUT variables.
"""
import argparse
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def run_tests(repo_root: Path, temp_dir: Path):
    xml_path = temp_dir / "junit.xml"
    cov_json_path = temp_dir / "coverage.json"

    cmd = [
        sys.executable,
        "-m",
        "coverage",
        "run",
        "--branch",
        "--source=admin,app,auth,db,engine,modes,scoring,ui",
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        f"--junitxml={xml_path}",
        "-q",
    ]

    start_time = time.perf_counter()
    res = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    duration = time.perf_counter() - start_time

    # Generate JSON coverage report
    subprocess.run(
        [sys.executable, "-m", "coverage", "json", "-o", str(cov_json_path)],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    return res.returncode, duration, xml_path, cov_json_path


def parse_junit_xml(xml_path: Path):
    if not xml_path.exists():
        return {"tests": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0}

    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Could be <testsuites> or <testsuite>
    tests = int(root.attrib.get("tests", 0))
    failures = int(root.attrib.get("failures", 0))
    errors = int(root.attrib.get("errors", 0))
    skipped = int(root.attrib.get("skipped", 0))

    if tests == 0 and len(root) > 0:
        for suite in root.iter("testsuite"):
            tests += int(suite.attrib.get("tests", 0))
            failures += int(suite.attrib.get("failures", 0))
            errors += int(suite.attrib.get("errors", 0))
            skipped += int(suite.attrib.get("skipped", 0))

    passed = max(0, tests - failures - errors - skipped)
    return {
        "tests": tests,
        "passed": passed,
        "failed": failures,
        "errors": errors,
        "skipped": skipped,
    }


def parse_coverage_json(cov_json_path: Path):
    if not cov_json_path.exists():
        return {
            "num_statements": 0,
            "covered_lines": 0,
            "missing_lines": 0,
            "num_branches": 0,
            "covered_branches": 0,
            "stmt_pct": 0.0,
            "branch_pct": 0.0,
            "combined_pct": 0.0,
            "files": [],
        }

    with open(cov_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    totals = data.get("totals", {})
    num_statements = totals.get("num_statements", 0)
    covered_lines = totals.get("covered_lines", 0)
    missing_lines = totals.get("missing_lines", 0)

    num_branches = totals.get("num_branches", 0)
    covered_branches = totals.get("covered_branches", 0)
    missing_branches = totals.get("missing_branches", 0)
    partial_branches = totals.get("num_partial_branches", 0)

    stmt_pct = (covered_lines / num_statements * 100.0) if num_statements > 0 else 0.0
    branch_pct = (covered_branches / num_branches * 100.0) if num_branches > 0 else 0.0
    combined_pct = totals.get("percent_covered", 0.0)

    files_list = []
    files_dict = data.get("files", {})
    for file_path, file_info in sorted(files_dict.items()):
        summary = file_info.get("summary", {})
        f_stmts = summary.get("num_statements", 0)
        f_miss = summary.get("missing_lines", 0)
        f_branch = summary.get("num_branches", 0)
        f_brpart = summary.get("num_partial_branches", 0)
        f_cov = summary.get("percent_covered", 0.0)
        # make file path relative for display
        norm_path = os.path.normpath(file_path).replace("\\", "/")
        files_list.append({
            "path": norm_path,
            "stmts": f_stmts,
            "miss": f_miss,
            "branch": f_branch,
            "brpart": f_brpart,
            "cov": f_cov,
        })

    return {
        "num_statements": num_statements,
        "covered_lines": covered_lines,
        "missing_lines": missing_lines,
        "num_branches": num_branches,
        "covered_branches": covered_branches,
        "missing_branches": missing_branches,
        "stmt_pct": stmt_pct,
        "branch_pct": branch_pct,
        "combined_pct": combined_pct,
        "files": files_list,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", type=float, default=80.0, help="Minimum coverage percentage gate")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent

    with tempfile.TemporaryDirectory(prefix="test-report-") as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        returncode, duration, xml_path, cov_json_path = run_tests(repo_root, temp_dir)
        test_stats = parse_junit_xml(xml_path)
        cov_stats = parse_coverage_json(cov_json_path)

    tests_run = test_stats["tests"]
    passed = test_stats["passed"]
    failed = test_stats["failed"]
    errors = test_stats["errors"]
    skipped = test_stats["skipped"]

    pass_rate = (passed / tests_run * 100.0) if tests_run > 0 else 0.0
    pass_badge = "✅ Pass" if (failed == 0 and errors == 0 and tests_run > 0) else "❌ Fail"

    stmt_cov_pct = cov_stats["stmt_pct"]
    covered_stmts = cov_stats["covered_lines"]
    total_stmts = cov_stats["num_statements"]

    branch_cov_pct = cov_stats["branch_pct"]
    covered_branches = cov_stats["covered_branches"]
    total_branches = cov_stats["num_branches"]

    combined_pct = cov_stats["combined_pct"]
    cov_gate_passed = combined_pct >= args.gate
    cov_badge = "✅ Pass" if cov_gate_passed else "❌ Fail"

    py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    os_name = "Windows" if platform.system() == "Windows" else platform.system()
    job_header = f"2 · Test ({os_name}, Python {py_version})"

    # Format file coverage table
    file_rows = []
    for f in cov_stats["files"]:
        file_rows.append(
            f"| `{f['path']}` | {f['stmts']} | {f['miss']} | {f['branch']} | {f['brpart']} | {f['cov']:.1f}% |"
        )
    files_table = "\n".join(file_rows)

    summary_md = f"""## {job_header} summary

### {job_header}

| Metric | Result |
|---|---|
| Tests run | **{tests_run}** |
| Passed | {passed} |
| Failed / errors | {failed} / {errors} |
| Skipped or expected failures | {skipped} |
| Pass rate | {pass_rate:.1f}% · {pass_badge} |
| Duration | {duration:.1f} s |
| Statement coverage | {stmt_cov_pct:.1f}% ({covered_stmts}/{total_stmts}) |
| Branch coverage | {branch_cov_pct:.1f}% ({covered_branches}/{total_branches}) |
| Combined coverage (gate ≥ {args.gate:.0f}%) | **{combined_pct:.1f}%** · {cov_badge} |

<details>
<summary>Coverage per file</summary>

| File | Statements | Miss | Branch | BrPart | Coverage |
|---|---|---|---|---|---|
{files_table}

</details>

<sub>Job summary generated at run-time</sub>
"""

    print(summary_md)

    step_summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary_file:
        with open(step_summary_file, "a", encoding="utf-8") as f:
            f.write(summary_md + "\n")

    summary_line = f"{passed}/{tests_run} passed ({pass_rate:.1f}%) · {failed + errors} failed"
    cov_summary_line = f"{combined_pct:.1f}% combined (statements {stmt_cov_pct:.1f}%, branches {branch_cov_pct:.1f}%) · gate ≥ {args.gate:.0f}%"

    github_output_file = os.environ.get("GITHUB_OUTPUT")
    if github_output_file:
        with open(github_output_file, "a", encoding="utf-8") as f:
            f.write(f"tests_run={tests_run}\n")
            f.write(f"passed={passed}\n")
            f.write(f"failed={failed}\n")
            f.write(f"errors={errors}\n")
            f.write(f"skipped={skipped}\n")
            f.write(f"pass_rate={pass_rate:.1f}\n")
            f.write(f"combined_cov={combined_pct:.1f}\n")
            f.write(f"stmt_cov={stmt_cov_pct:.1f}\n")
            f.write(f"branch_cov={branch_cov_pct:.1f}\n")
            f.write(f"duration={duration:.1f}\n")
            f.write(f"test_summary_line={summary_line}\n")
            f.write(f"cov_summary_line={cov_summary_line}\n")
            f.write(f"status={'success' if (failed == 0 and errors == 0 and cov_gate_passed) else 'failure'}\n")

    if failed > 0 or errors > 0 or not cov_gate_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()

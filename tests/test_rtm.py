"""S2-17: keeps docs/RTM.md honest.

The RTM claims which requirements are verified. These tests make sure the
claims point at things that really exist, so the matrix cannot quietly go
stale when files are renamed or removed.
"""
import re
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
RTM = ROOT / "docs" / "RTM.md"

# Requirement -> test case, exactly as in STP Appendix A / SRS section 8.
EXPECTED_TEST_CASES = {
    "SNAKE-F-001": "TC-AUTH-001", "SNAKE-F-002": "TC-AUTH-002",
    "SNAKE-F-003": "TC-PROFILE-001", "SNAKE-F-004": "TC-AUTH-003",
    "SNAKE-F-005": "TC-GAME-001", "SNAKE-F-006": "TC-MODE-001",
    "SNAKE-F-007": "TC-DIFF-001", "SNAKE-F-008": "TC-GAME-002",
    "SNAKE-F-009": "TC-MOVE-001", "SNAKE-F-010": "TC-FOOD-001",
    "SNAKE-F-011": "TC-FOOD-002", "SNAKE-F-012": "TC-COLLISION-001",
    "SNAKE-F-013": "TC-SCORE-001", "SNAKE-F-014": "TC-OBSTACLE-001",
    "SNAKE-F-015": "TC-POWERUP-001", "SNAKE-F-016": "TC-MULTI-001",
    "SNAKE-F-017": "TC-SURVIVAL-001", "SNAKE-F-018": "TC-CLASSIC-001",
    "SNAKE-F-019": "TC-SCORE-002", "SNAKE-F-020": "TC-LEADER-001",
    "SNAKE-NF-001": "TC-NF-PERF-001", "SNAKE-NF-002": "TC-NF-PERF-002",
    "SNAKE-NF-003": "TC-NF-REL-001", "SNAKE-NF-004": "TC-NF-USE-001",
    "SNAKE-NF-005": "TC-NF-MAIN-001", "SNAKE-NF-006": "TC-NF-COMP-001",
    "SNAKE-SR-001": "TC-SEC-001", "SNAKE-SR-002": "TC-SEC-002",
    "SNAKE-SR-003": "TC-SEC-003", "SNAKE-SR-004": "TC-SEC-004",
    "SNAKE-SR-005": "TC-SEC-005",
}


def load_rows():
    rows = []
    for line in RTM.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| SNAKE-"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        assert len(cells) == 7, "row should have 7 columns: %s" % line
        rows.append({
            "id": cells[0], "test_case": cells[3], "evidence": cells[4],
            "status": cells[5], "notes": cells[6],
        })
    return rows


def evidence_references(text):
    return re.findall(r"`([^`]+)`", text)


ROWS = load_rows()


def test_every_requirement_is_listed_exactly_once():
    assert [row["id"] for row in ROWS] == list(EXPECTED_TEST_CASES)


def test_test_case_ids_match_the_stp():
    for row in ROWS:
        assert row["test_case"] == EXPECTED_TEST_CASES[row["id"]], row["id"]


def test_status_codes_are_valid():
    assert {row["status"] for row in ROWS} <= {"N", "P", "A"}


@pytest.mark.parametrize("row", ROWS, ids=[r["id"] for r in ROWS])
def test_evidence_exists(row):
    for reference in evidence_references(row["evidence"]):
        path, _, name = reference.partition("::")
        target = ROOT / path
        assert target.is_file(), "%s: %s does not exist" % (row["id"], path)
        if name:
            source = target.read_text(encoding="utf-8")
            pattern = r"^\s*(class|def)\s+%s\b" % re.escape(name)
            assert re.search(pattern, source, re.MULTILINE), (
                "%s: %s not found in %s" % (row["id"], name, path))


@pytest.mark.parametrize("row", ROWS, ids=[r["id"] for r in ROWS])
def test_status_is_backed_by_evidence(row):
    if row["status"] == "A":
        assert evidence_references(row["evidence"]), (
            "%s is marked A but lists no evidence" % row["id"])
    if row["status"] == "P":
        assert row["notes"], "%s: say what is still missing" % row["id"]
    if row["status"] == "N":
        assert not evidence_references(row["evidence"]), (
            "%s is N but lists tests; should it be P?" % row["id"])


def test_summary_line_matches_the_table():
    counts = Counter(row["status"] for row in ROWS)
    expected = "Total %d requirements: A = %d, P = %d, N = %d" % (
        len(ROWS), counts["A"], counts["P"], counts["N"])
    assert expected in RTM.read_text(encoding="utf-8")


def test_security_test_cases_are_named_in_the_security_suite():
    suite = (ROOT / "tests" / "test_security_suite.py").read_text(
        encoding="utf-8")
    for case in ("TC-SEC-001", "TC-SEC-002", "TC-SEC-003", "TC-SEC-004",
                 "TC-SEC-005", "TC-AUTH-003", "TC-NF-REL-001"):
        assert case in suite, case

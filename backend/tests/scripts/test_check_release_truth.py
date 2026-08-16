from scripts.check_release_truth import authority_exclusive_errors, main


def test_current_repo_release_truth_is_consistent():
    assert main() == 0


def test_pr89_open_conflicts_with_merged_story():
    errors = authority_exclusive_errors(
        "docs/HANDOFF.md",
        "PR #89 OPEN after squash. PR #89 MERGED on main.",
    )
    assert errors


def test_pr89_open_conflicts_with_sha_pointer():
    errors = authority_exclusive_errors(
        "docs/PROGRESS_CHECKLIST.md",
        "PR **#89 OPEN** (until merged) · `#89`→`e05e29f`",
    )
    assert errors


def test_ee6597e_conflicts_with_89_merged():
    errors = authority_exclusive_errors(
        "docs/HANDOFF.md",
        "Last code `ee6597e` (PR **#89 MERGED**)",
    )
    assert errors


def test_merged_story_without_open_or_stale_sha_is_ok():
    assert (
        authority_exclusive_errors(
            "docs/HANDOFF.md",
            "Last code `e05e29f` (PR **#89 MERGED**)",
        )
        == []
    )

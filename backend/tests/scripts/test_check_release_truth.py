from scripts.check_release_truth import main


def test_current_repo_release_truth_is_consistent():
    assert main() == 0

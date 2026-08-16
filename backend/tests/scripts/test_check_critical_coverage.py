import json

from scripts.check_critical_coverage import main


def test_critical_coverage_passes_synthetic_report(tmp_path, monkeypatch, capsys):
    files = {}
    for rel, floor in {
        "app/core/security.py": 90,
        "app/core/session_policy.py": 90,
        "app/services/finance.py": 90,
        "app/api/v1/endpoints/finance.py": 90,
        "app/services/access.py": 90,
        "app/services/booking.py": 90,
        "app/services/data_import.py": 90,
        "app/services/dsar.py": 90,
        "app/workers/report.py": 90,
        "app/workers/notification.py": 90,
        "app/workers/outbox.py": 90,
        "app/workers/retention.py": 90,
    }.items():
        files[rel] = {"summary": {"percent_covered": float(floor)}}
    report = tmp_path / "coverage.json"
    report.write_text(json.dumps({"files": files}), encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv", ["check_critical_coverage.py", "--coverage", str(report)]
    )
    assert main() == 0


def test_critical_coverage_fails_when_report_missing(tmp_path, monkeypatch):
    missing = tmp_path / "nope.json"
    monkeypatch.setattr(
        "sys.argv", ["check_critical_coverage.py", "--coverage", str(missing)]
    )
    assert main() == 1

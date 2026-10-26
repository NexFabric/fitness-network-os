from scripts.smtp_delivery_proof import main


def test_smtp_proof_unverified_without_host(monkeypatch):
    monkeypatch.delenv("SMTP_HOST", raising=False)
    assert main() == 2

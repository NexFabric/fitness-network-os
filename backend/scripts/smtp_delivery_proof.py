#!/usr/bin/env python3
"""Send one SMTP probe message. Exit 2 when SMTP is not configured.

Local Mailpit/Mailhog is a valid adapter proof. DKIM/SPF/DMARC against a
real domain stays UNVERIFIED until an operator records them.
"""

from __future__ import annotations

import os
import smtplib
import ssl
from email.message import EmailMessage


def main() -> int:
    host = os.environ.get("SMTP_HOST", "").strip()
    if not host:
        print("SMTP proof: UNVERIFIED (SMTP_HOST unset)")
        return 2
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASS", "")
    from_addr = os.environ.get("SMTP_FROM", "noreply@localhost")
    to_addr = os.environ.get("SMTP_PROOF_TO", from_addr)
    starttls = os.environ.get("SMTP_STARTTLS", "1") != "0"

    msg = EmailMessage()
    msg["Subject"] = "GymClubNex SMTP proof"
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content("smtp delivery proof — no PII")

    context = ssl.create_default_context()
    ca_bundle = os.environ.get("SMTP_CA_BUNDLE")
    if ca_bundle:
        context.load_verify_locations(cafile=ca_bundle)

    with smtplib.SMTP(host, port, timeout=10) as server:
        if starttls:
            server.starttls(context=context)
        if user and password:
            server.login(user, password)
        server.send_message(msg)
    print(f"SMTP proof: sent via {host}:{port} to {to_addr}")
    print(
        "DKIM/SPF/DMARC: not asserted by this script — record in docs/ops/SMTP_PROOF.md"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

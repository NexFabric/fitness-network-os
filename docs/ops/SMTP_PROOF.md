# SMTP production proof

**Status:** **ADAPTER LANDED · DOMAIN PROOF UNVERIFIED**

## What the code does

`SmtpNotificationProvider` uses `smtplib` + `STARTTLS`. Production boot
requires `NOTIFICATION_EMAIL_PROVIDER=smtp` and `SMTP_HOST` / `SMTP_FROM`.

## Local adapter proof

```bash
# Mailpit / Mailhog on localhost:1025, no TLS
SMTP_HOST=127.0.0.1 SMTP_PORT=1025 SMTP_STARTTLS=0 \
SMTP_FROM=dev@localhost SMTP_PROOF_TO=dev@localhost \
uv run python scripts/smtp_delivery_proof.py
```

A successful local send is **adapter proof**, not production proof.

## Production checklist (human)

- [ ] Real provider accepted the message
- [ ] SPF published
- [ ] DKIM signing on
- [ ] DMARC policy recorded
- [ ] Auth rejection path observed
- [ ] Bounce / retry observed on the notification worker

Until those boxes are ticked this file stays UNVERIFIED.

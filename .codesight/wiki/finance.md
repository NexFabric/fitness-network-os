# Finance

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Finance subsystem handles **14 routes**.

## Routes

- `POST` `/billing-accounts` → in: BillingAccountCreate, out: BillingAccountResponse
  `backend/app/api/v1/endpoints/finance.py`
- `POST` `/invoices` → in: BillingAccountCreate, out: BillingAccountResponse
  `backend/app/api/v1/endpoints/finance.py`
- `POST` `/invoices/{invoice_id}/issue` params(invoice_id) → in: BillingAccountCreate, out: BillingAccountResponse
  `backend/app/api/v1/endpoints/finance.py`
- `POST` `/invoices/{invoice_id}/void` params(invoice_id) → in: BillingAccountCreate, out: BillingAccountResponse
  `backend/app/api/v1/endpoints/finance.py`
- `POST` `/payments` → in: BillingAccountCreate, out: BillingAccountResponse
  `backend/app/api/v1/endpoints/finance.py`
- `POST` `/payments/{payment_id}/refunds` params(payment_id) → in: BillingAccountCreate, out: BillingAccountResponse
  `backend/app/api/v1/endpoints/finance.py`
- `POST` `/credits` → in: BillingAccountCreate, out: BillingAccountResponse
  `backend/app/api/v1/endpoints/finance.py`
- `POST` `/credits/{credit_id}/apply` params(credit_id) → in: BillingAccountCreate, out: BillingAccountResponse
  `backend/app/api/v1/endpoints/finance.py`
- `POST` `/discounts` → in: BillingAccountCreate, out: BillingAccountResponse
  `backend/app/api/v1/endpoints/finance.py`
- `POST` `/reconciliations` → in: BillingAccountCreate, out: BillingAccountResponse
  `backend/app/api/v1/endpoints/finance.py`
- `POST` `/reconciliations/items/{item_id}/match` params(item_id) → in: BillingAccountCreate, out: BillingAccountResponse
  `backend/app/api/v1/endpoints/finance.py`
- `POST` `/reconciliations/{run_id}/complete` params(run_id) → in: BillingAccountCreate, out: BillingAccountResponse
  `backend/app/api/v1/endpoints/finance.py`
- `GET` `/invoices` → out: BillingAccountResponse
  `backend/app/api/v1/endpoints/finance.py`
- `GET` `/payments` → out: BillingAccountResponse
  `backend/app/api/v1/endpoints/finance.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend/app/api/v1/endpoints/finance.py`

---
_Back to [overview.md](./overview.md)_
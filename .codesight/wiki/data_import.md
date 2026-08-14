# Data_import

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Data_import subsystem handles **4 routes** and touches: auth, db.

## Routes

- `POST` `/upload` → in: CsvUploadRequest, out: ImportBatchResponse [auth, upload]
  `backend/app/api/v1/endpoints/data_import.py`
- `GET` `/batches` → in: AsyncSessio, out: ImportBatchResponse [auth, db]
  `backend/app/api/v1/endpoints/data_import.py`
- `GET` `/batch/{batch_id}` params(batch_id) → in: AsyncSessio, out: ImportBatchResponse [auth, db]
  `backend/app/api/v1/endpoints/data_import.py`
- `POST` `/batch/{batch_id}/commit` params(batch_id) → in: CsvUploadRequest, out: ImportBatchResponse [auth]
  `backend/app/api/v1/endpoints/data_import.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend/app/api/v1/endpoints/data_import.py`

---
_Back to [overview.md](./overview.md)_
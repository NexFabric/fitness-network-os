import csv
import io
import re
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_import import (
    DataImportBatch,
    DataImportRow,
    ImportBatchStatus,
    ImportRowStatus,
)
from app.models.member import Member
from app.models.membership import Membership, PlanVersion


def _normalize_header(header: str) -> str:
    h = header.strip().lower().replace(" ", "_")
    mapping = {
        "ad": "first_name",
        "isim": "first_name",
        "soyad": "last_name",
        "soyisim": "last_name",
        "eposta": "email",
        "e-posta": "email",
        "telefon": "phone",
        "tel": "phone",
        "gsm": "phone",
        "uye_no": "member_number",
        "kart_no": "member_number",
        "plan": "plan_id",
        "paket": "plan_id",
        "baslangic": "start_date",
        "tarih": "start_date",
    }
    return mapping.get(h, h)


class DataImportService:
    @staticmethod
    async def create_preview_batch(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        filename: str,
        csv_text: str,
    ) -> DataImportBatch:
        f = io.StringIO(csv_text.strip())
        reader = csv.reader(f)
        try:
            raw_headers = next(reader)
        except StopIteration:
            raise ValueError("CSV dosyası boş veya geçersiz.")

        headers = [_normalize_header(h) for h in raw_headers]
        if "first_name" not in headers or "last_name" not in headers:
            raise ValueError("CSV dosyasında en azından 'first_name'/'ad' ve 'last_name'/'soyad' sütunları bulunmalıdır.")

        batch = DataImportBatch(
            id=uuid4(),
            tenant_id=tenant_id,
            filename=filename,
            status=ImportBatchStatus.PREVIEW,
            created_by_user_id=user_id,
        )
        db.add(batch)
        await db.flush()

        total = 0
        valid = 0
        invalid = 0
        email_regex = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

        for idx, row in enumerate(reader, start=1):
            if not row or all(c.strip() == "" for c in row):
                continue
            total += 1
            row_dict = {}
            for col_idx, val in enumerate(row):
                if col_idx < len(headers):
                    row_dict[headers[col_idx]] = val.strip()

            # Validation
            first_name = row_dict.get("first_name", "").strip()
            last_name = row_dict.get("last_name", "").strip()
            email = row_dict.get("email", "").strip() or None
            phone = row_dict.get("phone", "").strip() or None
            member_number = row_dict.get("member_number", "").strip() or None

            errors = []
            if not first_name:
                errors.append("İsim (first_name) boş olamaz.")
            if not last_name:
                errors.append("Soyisim (last_name) boş olamaz.")
            if email and not email_regex.match(email):
                errors.append("Geçersiz e-posta formatı.")

            status = ImportRowStatus.INVALID if errors else ImportRowStatus.VALID
            if status == ImportRowStatus.VALID:
                valid += 1
            else:
                invalid += 1

            parsed = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": phone,
                "member_number": member_number,
                "plan_id": row_dict.get("plan_id"),
                "start_date": row_dict.get("start_date"),
            }

            import_row = DataImportRow(
                id=uuid4(),
                tenant_id=tenant_id,
                batch_id=batch.id,
                row_number=idx,
                status=status,
                raw_data=row_dict,
                parsed_data=parsed,
                error_message="; ".join(errors) if errors else None,
            )
            db.add(import_row)

        batch.total_rows = total
        batch.valid_rows = valid
        batch.invalid_rows = invalid
        await db.commit()
        await db.refresh(batch)
        return batch

    @staticmethod
    async def commit_batch(
        db: AsyncSession,
        tenant_id: UUID,
        batch_id: UUID,
    ) -> DataImportBatch:
        batch = await db.get(DataImportBatch, batch_id)
        if not batch or batch.tenant_id != tenant_id:
            raise ValueError("İçe aktarma grubu bulunamadı.")
        if batch.status != ImportBatchStatus.PREVIEW:
            raise ValueError("Bu içe aktarma grubu zaten işlendi veya geçersiz durumda.")

        batch.status = ImportBatchStatus.PROCESSING
        await db.commit()

        # Fetch valid rows
        rows_res = await db.execute(
            select(DataImportRow)
            .where(
                DataImportRow.batch_id == batch_id,
                DataImportRow.tenant_id == tenant_id,
                DataImportRow.status == ImportRowStatus.VALID,
            )
            .order_by(DataImportRow.row_number)
        )
        valid_rows = list(rows_res.scalars().all())

        imported_count = 0
        for row in valid_rows:
            parsed = row.parsed_data or {}
            mbr_num = parsed.get("member_number") or f"IMP-{uuid4().hex[:6].upper()}"

            # Check duplicate member_number
            existing = (
                await db.execute(
                    select(Member).where(
                        Member.tenant_id == tenant_id,
                        Member.member_number == mbr_num,
                    )
                )
            ).scalar_one_or_none()
            if existing:
                mbr_num = f"{mbr_num}-{uuid4().hex[:4].upper()}"

            member = Member(
                id=uuid4(),
                tenant_id=tenant_id,
                member_number=mbr_num,
                first_name=parsed["first_name"],
                last_name=parsed["last_name"],
                email=parsed.get("email"),
                phone=parsed.get("phone"),
                status="ACTIVE",
            )
            db.add(member)
            await db.flush()

            # If plan_id given, attach membership if plan version exists
            if parsed.get("plan_id"):
                try:
                    plan_uuid = UUID(parsed["plan_id"])
                    pv = (
                        await db.execute(
                            select(PlanVersion)
                            .where(
                                PlanVersion.tenant_id == tenant_id,
                                PlanVersion.plan_id == plan_uuid,
                            )
                            .order_by(PlanVersion.version.desc())
                        )
                    ).scalars().first()

                    if pv:
                        membership = Membership(
                            id=uuid4(),
                            tenant_id=tenant_id,
                            member_id=member.id,
                            plan_version_id=pv.id,
                            status="ACTIVE",
                            start_date=datetime.now(UTC),
                        )
                        db.add(membership)
                except Exception:
                    pass

            row.status = ImportRowStatus.IMPORTED
            imported_count += 1

        batch.imported_rows = imported_count
        batch.status = ImportBatchStatus.COMPLETED
        batch.completed_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(batch)
        return batch

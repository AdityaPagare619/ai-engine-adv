"""
CSV Import & Validation Router
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from typing import Dict
import uuid
import pandas as pd

from app import get_db_pool
from services.shared.checksum import compute_checksum
from services.shared.csv_validator import validate_csv
from services.content_processor.app import CSVImportResponse

router = APIRouter()

@router.post("/import/csv", response_model=CSVImportResponse, status_code=201)
async def import_csv(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = Depends(),
    pool=Depends(get_db_pool)
):
    # Validate extension
    if not file.filename.lower().endswith(tuple((".csv",))):
        raise HTTPException(400, "Only CSV allowed")

    data = await file.read()
    checksum = compute_checksum(data)
    operation_id = str(uuid.uuid4())

    # Save temp file
    temp_path = f"/tmp/{operation_id}.csv"
    with open(temp_path, "wb") as f:
        f.write(data)

    # Validate headers
    df = pd.read_csv(temp_path, nrows=0)
    missing = validate_csv(df.columns.tolist())
    if missing:
        raise HTTPException(422, f"Missing columns: {', '.join(missing)}")

    # Schedule background processing
    background_tasks.add_task(process_csv, temp_path, checksum, operation_id)

    return CSVImportResponse(
        operation_id=operation_id,
        sheet_id="pending",
        total_rows=0,
        imported=0,
        skipped=0,
        errors=0
    )

async def process_csv(path: str, checksum: str, operation_id: str):
    """
    Background CSV processing:
    - Check duplicate
    - Batch insert
    - Update import_operations table
    """
    pool = await get_db_pool()
    df = pd.read_csv(path)

    total = len(df)
    imported = skipped = errors = 0
    sheet_id = None

    async with pool.acquire() as conn:
        # Check duplicate sheet via checksum
        row = await conn.fetchrow(
            "SELECT sheet_id FROM question_sheets WHERE file_checksum=$1", checksum
        )
        if row:
            sheet_id = row["sheet_id"]
            # Increment version and process incremental update...
        else:
            # Generate sheet_id, insert question_sheets record...
            sheet_id = f"SHT-{operation_id[:8]}"
            await conn.execute(
                """
                INSERT INTO question_sheets (
                    sheet_id, subject_id, sheet_name, file_path, file_checksum, total_questions, import_status
                ) VALUES ($1, $2, $3, $4, $5, $6, 'PROCESSING')
                """,
                sheet_id, "subject_pending", path, path, checksum, total
            )
        # Loop rows and insert questions...
        # For brevity, demo logic omitted.

    # Finalize import_operations record...

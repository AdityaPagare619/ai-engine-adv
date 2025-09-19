"""
Incremental CSV Update Router
Handles uploads of updated CSV sheets to add/update questions
"""
import os
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app import get_db_pool
from app import compute_checksum, validate_csv
from pydantic import BaseModel

router = APIRouter()

class CSVUpdateResponse(BaseModel):
    operation_id: str
    sheet_id: str
    added: int
    updated: int
    skipped: int
    errors: int

@router.post("/update/csv", response_model=CSVUpdateResponse)
async def update_csv(
    file: UploadFile = File(...),
    pool: AsyncSession = Depends(get_db_pool)
):
    # Validate extension
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Only CSV files allowed")
    data = await file.read()
    checksum = compute_checksum(data)

    # Save file
    op_id = checksum[:8]
    temp_path = f"uploads/{op_id}.csv"
    os.makedirs("uploads", exist_ok=True)
    with open(temp_path, "wb") as f:
        f.write(data)

    # Validate headers
    df_head = pd.read_csv(temp_path, nrows=0)
    missing = validate_csv(df_head.columns.tolist())
    if missing:
        raise HTTPException(422, f"Missing columns: {', '.join(missing)}")

    # Load full DataFrame
    df = pd.read_csv(temp_path)
    added = updated = skipped = errors = 0

    async with pool.acquire() as conn:
        # Determine sheet_id by checksum
        sheet_id = await conn.fetchval(
            "SELECT sheet_id FROM question_sheets WHERE file_checksum=$1", checksum
        )
        if not sheet_id:
            raise HTTPException(404, "Original sheet not found; please import first")

        for idx, row in df.iterrows():
            qid = f"{sheet_id}-Q-{int(row['question_number']):05d}"
            try:
                exists = await conn.fetchval(
                    "SELECT 1 FROM questions WHERE question_id=$1", qid
                )
                if exists:
                    # Update existing question
                    await conn.execute(
                        """
                        UPDATE questions SET
                          question_text=$2,
                          correct_option=$3,
                          updated_at=NOW()
                        WHERE question_id=$1
                        """,
                        qid, row['question_text'], str(row['correct_option_number'])
                    )
                    updated += 1
                else:
                    # Insert new question
                    await conn.execute(
                        """
                        INSERT INTO questions (
                          question_id, sheet_id, question_number,
                          question_text, correct_option
                        ) VALUES ($1,$2,$3,$4,$5)
                        """,
                        qid, sheet_id, str(row['question_number']),
                        row['question_text'], str(row['correct_option_number'])
                    )
                    added += 1
            except Exception:
                errors += 1

    return CSVUpdateResponse(
        operation_id=op_id,
        sheet_id=sheet_id,
        added=added,
        updated=updated,
        skipped=skipped,
        errors=errors
    )

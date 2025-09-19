"""
Content Processor Service - FastAPI App
Handles CSV import, validation, and incremental updates
"""
import os
import sys
import uuid
import hashlib
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import asyncpg
import structlog


# Setup logger directly
logger = structlog.get_logger()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://jee_admin:secure_jee_2025@postgres:5432/jee_smart_platform")

# Upload directory
UPLOAD_DIR = "uploads"

# CSV required columns
CSV_REQUIRED_COLUMNS = [
    "question_number", "question_text",
    "option_1_text", "option_2_text", "option_3_text", "option_4_text",
    "correct_option_number"
]

# Database pool
db_pool: asyncpg.Pool = None

async def get_db_pool():
    global db_pool
    if not db_pool:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    return db_pool

# Utility functions (inline to avoid import issues)
def compute_checksum(data: bytes) -> str:
    """Compute SHA256 checksum"""
    return hashlib.sha256(data).hexdigest()

def validate_csv(columns: list) -> list:
    """Return missing required columns"""
    return [col for col in CSV_REQUIRED_COLUMNS if col not in columns]

app = FastAPI(
    title="Content Processor Service",
    description="CSV import & validation for Smart Database System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    """Startup event"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    await get_db_pool()
    logger.info("Content Processor Service started")

@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {
            "status": "healthy",
            "service": "content-processor",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )

# Pydantic schemas
class CSVImportResponse(BaseModel):
    operation_id: str
    sheet_id: str
    total_rows: int
    imported: int
    skipped: int
    errors: int

class ImportStatusResponse(BaseModel):
    operation_id: str
    status: str
    total_rows: int
    imported_rows: int
    skipped_rows: int
    error_count: int
    started_at: str
    completed_at: Optional[str] = None

@app.post("/content/import/csv", response_model=CSVImportResponse, status_code=201)
async def import_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """Import CSV file"""
    try:
        # Validate file extension
        if not file.filename.lower().endswith(".csv"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only CSV files are allowed"
            )

        # Read file data
        data = await file.read()
        if len(data) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file uploaded"
            )

        # Generate operation ID and checksum
        checksum = compute_checksum(data)
        operation_id = str(uuid.uuid4())

        # Save file to uploads directory
        save_path = os.path.join(UPLOAD_DIR, f"{operation_id}.csv")
        with open(save_path, "wb") as f:
            f.write(data)

        # Validate CSV structure
        try:
            df_head = pd.read_csv(save_path, nrows=0)
            missing_columns = validate_csv(df_head.columns.tolist())

            if missing_columns:
                # Cleanup file
                os.remove(save_path)
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Missing required columns: {', '.join(missing_columns)}"
                )
        except pd.errors.EmptyDataError:
            os.remove(save_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file is empty or invalid"
            )

        # Get total rows
        df_full = pd.read_csv(save_path)
        total_rows = len(df_full)

        # Record import operation in database
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO import_operations (
                    operation_id, operation_type, initiated_by, source_file,
                    status, total_rows
                ) VALUES ($1, $2, $3, $4, $5, $6)
                """,
                operation_id, 'CSV_IMPORT', 'system_admin', save_path,
                'IN_PROGRESS', total_rows
            )

        # Schedule background processing
        background_tasks.add_task(process_csv_background, operation_id, save_path, checksum)

        logger.info(
            "CSV import initiated",
            operation_id=operation_id,
            filename=file.filename,
            total_rows=total_rows
        )

        return CSVImportResponse(
            operation_id=operation_id,
            sheet_id="processing",
            total_rows=total_rows,
            imported=0,
            skipped=0,
            errors=0
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("CSV import failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )

async def process_csv_background(operation_id: str, file_path: str, checksum: str):
    """Background task to process CSV file"""
    try:
        pool = await get_db_pool()
        df = pd.read_csv(file_path)
        total_rows = len(df)
        imported = skipped = errors = 0

        # Generate sheet ID
        sheet_id = f"SHT-{operation_id[:8].upper()}"

        async with pool.acquire() as conn:
            # Check if sheet with same checksum exists
            existing_sheet = await conn.fetchval(
                "SELECT sheet_id FROM question_sheets WHERE file_checksum = $1",
                checksum
            )

            if existing_sheet:
                sheet_id = existing_sheet
                logger.info("Found existing sheet with same checksum", sheet_id=sheet_id)
            else:
                # Create new question sheet record
                await conn.execute(
                    """
                    INSERT INTO question_sheets (
                        sheet_id, sheet_name, file_path, file_checksum,
                        subject_id, total_questions, import_status
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    sheet_id, os.path.basename(file_path), file_path, checksum,
                    'EXM-2025-JEE_MAIN-001-SUB-PHY', total_rows, 'PROCESSING'
                )

            # Process each question
            for index, row in df.iterrows():
                try:
                    question_id = f"{sheet_id}-Q-{int(row['question_number']):05d}"

                    # Check if question already exists
                    existing = await conn.fetchval(
                        "SELECT 1 FROM questions WHERE question_id = $1",
                        question_id
                    )

                    if existing:
                        skipped += 1
                        continue

                    # Insert new question
                    await conn.execute(
                        """
                        INSERT INTO questions (
                            question_id, sheet_id, subject_id, question_number,
                            question_text, correct_option
                        ) VALUES ($1, $2, $3, $4, $5, $6)
                        """,
                        question_id, sheet_id, 'EXM-2025-JEE_MAIN-001-SUB-PHY',
                        str(row['question_number']), str(row['question_text']),
                        str(row['correct_option_number'])
                    )

                    # Insert question options
                    for opt_num in range(1, 5):
                        option_id = f"{question_id}-OPT-{opt_num}"
                        option_text = str(row[f'option_{opt_num}_text'])
                        is_correct = (int(row['correct_option_number']) == opt_num)

                        await conn.execute(
                            """
                            INSERT INTO question_options (
                                option_id, question_id, option_number,
                                option_text, is_correct
                            ) VALUES ($1, $2, $3, $4, $5)
                            """,
                            option_id, question_id, opt_num, option_text, is_correct
                        )

                    imported += 1

                except Exception as e:
                    errors += 1
                    logger.error("Error processing question", row=index, error=str(e))

            # Update import operation status
            await conn.execute(
                """
                UPDATE import_operations SET
                    status = 'COMPLETED',
                    imported_rows = $2,
                    skipped_rows = $3,
                    error_count = $4,
                    completed_at = NOW()
                WHERE operation_id = $1
                """,
                operation_id, imported, skipped, errors
            )

            # Update question sheet status
            if not existing_sheet:
                await conn.execute(
                    """
                    UPDATE question_sheets SET
                        import_status = 'COMPLETED',
                        imported_questions = $2,
                        failed_questions = $3,
                        last_imported_at = NOW()
                    WHERE sheet_id = $1
                    """,
                    sheet_id, imported, errors
                )

        logger.info(
            "CSV processing completed",
            operation_id=operation_id,
            sheet_id=sheet_id,
            imported=imported,
            skipped=skipped,
            errors=errors
        )

    except Exception as e:
        # Update operation status to failed
        try:
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE import_operations SET
                        status = 'FAILED',
                        error_count = $2,
                        completed_at = NOW()
                    WHERE operation_id = $1
                    """,
                    operation_id, 1
                )
        except:
            pass

        logger.error("CSV processing failed", operation_id=operation_id, error=str(e))

@app.get("/content/import/status/{operation_id}", response_model=ImportStatusResponse)
async def get_import_status(operation_id: str):
    """Get import operation status"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT operation_id, status, total_rows, imported_rows,
                       skipped_rows, error_count, started_at, completed_at
                FROM import_operations 
                WHERE operation_id = $1
                """,
                operation_id
            )

            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Import operation not found"
                )

            return ImportStatusResponse(
                operation_id=row['operation_id'],
                status=row['status'],
                total_rows=row['total_rows'] or 0,
                imported_rows=row['imported_rows'] or 0,
                skipped_rows=row['skipped_rows'] or 0,
                error_count=row['error_count'] or 0,
                started_at=str(row['started_at']),
                completed_at=str(row['completed_at']) if row['completed_at'] else None
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving import status", operation_id=operation_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve import status"
        )

@app.get("/content/sheets")
async def list_sheets():
    """List all question sheets"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT sheet_id, sheet_name, total_questions, 
                       imported_questions, import_status, created_at
                FROM question_sheets 
                ORDER BY created_at DESC
                """
            )

            return {
                "sheets": [
                    {
                        "sheet_id": row['sheet_id'],
                        "sheet_name": row['sheet_name'],
                        "total_questions": row['total_questions'],
                        "imported_questions": row['imported_questions'],
                        "import_status": row['import_status'],
                        "created_at": str(row['created_at'])
                    }
                    for row in rows
                ]
            }

    except Exception as e:
        logger.error("Error listing sheets", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list sheets"
        )

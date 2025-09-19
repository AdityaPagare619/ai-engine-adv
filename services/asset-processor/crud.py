"""
Asset Processor CRUD Operations
"""
import os
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from services.asset_processor.models import QuestionAsset

async def create_asset_record(
    db: AsyncSession,
    asset_id: str,
    question_id: str,
    asset_type: str,
    asset_role: str,
    original_filename: str,
    storage_path: str,
    mime_type: str,
    file_size: int
) -> QuestionAsset:
    asset = QuestionAsset(
        asset_id=asset_id,
        question_id=question_id,
        asset_type=asset_type,
        asset_role=asset_role,
        original_filename=original_filename,
        storage_path=storage_path,
        mime_type=mime_type,
        file_size_bytes=file_size
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset

async def get_asset(db: AsyncSession, asset_id: str) -> QuestionAsset:
    result = await db.execute(
        select(QuestionAsset).where(QuestionAsset.asset_id == asset_id)
    )
    return result.scalar_one_or_none()

async def update_asset_formats(
    db: AsyncSession, asset_id: str, formats: dict, dimensions: dict
):
    asset = await get_asset(db, asset_id)
    if not asset:
        return None
    asset.formats = formats
    asset.dimensions = dimensions
    asset.processing_status = "COMPLETED"
    await db.commit()
    await db.refresh(asset)
    return asset

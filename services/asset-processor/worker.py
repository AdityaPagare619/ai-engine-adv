"""
Background worker to process pending assets
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models import Asset
from utils.image_processor import convert_to_webp, get_image_dimensions
import os

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def process_pending_assets():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            "SELECT asset_id, file_path FROM assets WHERE processing_status='PENDING'"
        )
        assets = result.fetchall()

        for asset_id, path in assets:
            try:
                raw = open(path, "rb").read()
                webp = convert_to_webp(raw)
                dims = get_image_dimensions(raw)
                webp_path = path + ".webp"
                with open(webp_path, "wb") as f:
                    f.write(webp)

                await session.execute(
                    """
                    UPDATE assets SET
                      formats = formats || $2,
                      dimensions = $3,
                      processing_status = 'COMPLETED',
                      updated_at = NOW()
                    WHERE asset_id = $1
                    """,
                    asset_id, {"webp": webp_path}, dims
                )
                await session.commit()
            except Exception:
                await session.rollback()
                continue

async def run_worker():
    while True:
        await process_pending_assets()
        await asyncio.sleep(30)  # Poll every 30s

if __name__ == "__main__":
    asyncio.run(run_worker())

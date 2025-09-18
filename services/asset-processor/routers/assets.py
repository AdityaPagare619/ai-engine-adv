from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
import os
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from crud import create_asset, get_asset, update_asset_processing
from utils.image_processor import convert_to_webp, get_image_dimensions
from app import get_db_pool

router = APIRouter()

UPLOAD_DIR = "uploads/assets"

@router.post("/upload", status_code=201)
async def upload_asset(question_id: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if file.content_type not in ["image/png", "image/jpeg", "image/webp"]:
        raise HTTPException(400, "Unsupported file type")

    asset_id = str(uuid.uuid4())
    filename = f"{asset_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    file_size = len(contents)
    mime_type = file.content_type
    dimensions = get_image_dimensions(contents)

    asset_record = await create_asset(db, {
        "asset_id": asset_id,
        "question_id": question_id,
        "asset_type": "IMAGE",
        "role": "MAIN",
        "filename": file.filename,
        "file_path": file_path,
        "mime_type": mime_type,
        "file_size": file_size,
        "dimensions": dimensions,
        "formats": {},
        "processing_status": "PENDING"
    })
    return {"asset_id": asset_id, "status": "Uploaded"}

@router.post("/process/{asset_id}")
async def process_asset(asset_id: str, db: AsyncSession = Depends(get_db)):
    asset = await get_asset(db, asset_id)
    if not asset:
        raise HTTPException(404, "Asset not found")

    if asset.processing_status == "COMPLETED":
        return {"status": "Already processed"}

    with open(asset.file_path, "rb") as f:
        contents = f.read()

    webp_data = convert_to_webp(contents)
    webp_path = asset.file_path + ".webp"

    with open(webp_path, "wb") as f:
        f.write(webp_data)

    dimensions = get_image_dimensions(contents)

    updated_asset = await update_asset_processing(db, asset_id,
                                                  {"original": asset.file_path, "webp": webp_path},
                                                  dimensions)
    return {"status": "Processed", "asset_id": asset_id}

@router.get("/download/{asset_id}/{format}")
async def download_asset(asset_id: str, format: str, db: AsyncSession = Depends(get_db)):
    asset = await get_asset(db, asset_id)
    if not asset:
        raise HTTPException(404, "Asset not found")

    path = asset.formats.get(format)
    if not path or not os.path.exists(path):
        raise HTTPException(404, f"Format '{format}' not found")

    return FileResponse(path)

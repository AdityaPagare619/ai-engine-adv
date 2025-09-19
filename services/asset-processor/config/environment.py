import os
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List

class AssetProcessorSettings(BaseSettings):
    ALLOWED_IMAGE_FORMATS: List[str] = Field(default=["png", "jpeg", "jpg", "webp", "svg"])
    OPTIMIZATION_LEVEL: str = Field(default="STANDARD")
    UPLOAD_DIR: str = Field(default="uploads/assets")
    ENV_FILE: str = Field(default=".env")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

asset_settings = AssetProcessorSettings()

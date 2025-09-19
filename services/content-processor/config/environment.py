"""
Content Processor-specific environment settings
"""
import os
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List

class ContentSettings(BaseSettings):
    MAX_UPLOAD_SIZE: int = Field(default=50_000_000)
    ALLOWED_EXTENSIONS: List[str] = Field(default=["csv"])
    CSV_REQUIRED_COLUMNS: List[str] = Field(default=[
        "question_number","question_text",
        "option_1_text","option_2_text","option_3_text","option_4_text",
        "correct_option_number"
    ])
    UPLOAD_DIR: str = Field(default="uploads")
    ENV_FILE: str = Field(default=".env")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

content_settings = ContentSettings()

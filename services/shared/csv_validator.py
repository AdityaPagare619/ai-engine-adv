"""
Validate CSV required columns
"""
from config.environment import content_settings

def validate_csv(columns: list[str]) -> list[str]:
    missing = [col for col in content_settings.CSV_REQUIRED_COLUMNS if col not in columns]
    return missing

"""
Industry-Grade ID Generation System
Hierarchical, collision-free ID generation following enterprise patterns
"""

import asyncio
import hashlib
from typing import Dict, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.orm import Session
import structlog

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from config.database import get_redis_client
from config.logging import logger

class IndustryIDGenerator:
    """
    Industry-standard hierarchical ID generation system
    Generates collision-free IDs following enterprise patterns used by NTA, ETS, etc.
    """

    def __init__(self):
        self.redis_client = get_redis_client()
        self.logger = logger

        # ID Format Templates
        self.templates = {
            "exam": "EXM-{year}-{type}-{seq:03d}",
            "subject": "{exam_id}-SUB-{code}",
            "sheet": "{subject_id}-SHT-V{version:02d}",
            "question": "{sheet_id}-Q-{seq:05d}",
            "option": "{question_id}-OPT-{number}",
            "asset": "{parent_id}-AST-{type}-{seq:03d}"
        }

        # Sequence keys for Redis
        self.sequence_keys = {
            "exam": "seq:exam:{year}:{type}",
            "question": "seq:question:{sheet_id}",
            "asset": "seq:asset:{parent_id}:{type}"
        }

    async def generate_exam_id_async(self, academic_year: int, exam_type: str, db: Session) -> str:
        """
        Generate unique exam ID: EXM-2025-JEE_MAIN-001
        """
        try:
            # Normalize exam type
            exam_type = exam_type.upper().replace(" ", "_")

            # Get next sequence number from database
            sequence_key = f"EXAM_{academic_year}_{exam_type}"
            next_seq = await self._get_next_sequence_db(db, "EXAM_ID", sequence_key)

            # Generate ID
            exam_id = self.templates["exam"].format(
                year=academic_year,
                type=exam_type,
                seq=next_seq
            )

            # Cache in Redis for fast lookups
            await self._cache_id_mapping("exam", exam_id, {
                "year": academic_year,
                "type": exam_type,
                "sequence": next_seq
            })

            self.logger.info(
                "Generated exam ID",
                exam_id=exam_id,
                year=academic_year,
                type=exam_type,
                sequence=next_seq
            )

            return exam_id

        except Exception as e:
            self.logger.error("Error generating exam ID", error=str(e))
            raise

    def generate_exam_id(self, academic_year: int, exam_type: str) -> str:
        """Synchronous version of exam ID generation"""
        exam_type = exam_type.upper().replace(" ", "_")

        # Simple sequence generation for sync version
        redis_key = f"seq:exam:{academic_year}:{exam_type}"
        next_seq = self.redis_client.incr(redis_key)

        exam_id = self.templates["exam"].format(
            year=academic_year,
            type=exam_type,
            seq=next_seq
        )

        return exam_id

    async def generate_subject_id_async(self, exam_id: str, subject_code: str, db: Session) -> str:
        """
        Generate unique subject ID: EXM-2025-JEE_MAIN-001-SUB-PHY
        """
        try:
            subject_code = subject_code.upper()

            # Validate exam_id exists
            if not await self._validate_parent_id(db, "exam_registry", "exam_id", exam_id):
                raise ValueError(f"Exam ID {exam_id} does not exist")

            subject_id = self.templates["subject"].format(
                exam_id=exam_id,
                code=subject_code
            )

            # Cache mapping
            await self._cache_id_mapping("subject", subject_id, {
                "exam_id": exam_id,
                "subject_code": subject_code
            })

            self.logger.info(
                "Generated subject ID",
                subject_id=subject_id,
                exam_id=exam_id,
                subject_code=subject_code
            )

            return subject_id

        except Exception as e:
            self.logger.error("Error generating subject ID", error=str(e))
            raise

    def generate_subject_id(self, exam_id: str, subject_code: str) -> str:
        """Synchronous version of subject ID generation"""
        subject_code = subject_code.upper()
        return self.templates["subject"].format(exam_id=exam_id, code=subject_code)

    async def generate_sheet_id_async(self, subject_id: str, version: int, db: Session) -> str:
        """
        Generate unique sheet ID: EXM-2025-JEE_MAIN-001-SUB-PHY-SHT-V01
        """
        try:
            # Validate subject_id exists
            if not await self._validate_parent_id(db, "subject_registry", "subject_id", subject_id):
                raise ValueError(f"Subject ID {subject_id} does not exist")

            sheet_id = self.templates["sheet"].format(
                subject_id=subject_id,
                version=version
            )

            await self._cache_id_mapping("sheet", sheet_id, {
                "subject_id": subject_id,
                "version": version
            })

            self.logger.info(
                "Generated sheet ID",
                sheet_id=sheet_id,
                subject_id=subject_id,
                version=version
            )

            return sheet_id

        except Exception as e:
            self.logger.error("Error generating sheet ID", error=str(e))
            raise

    def generate_sheet_id(self, subject_id: str, version: int = 1) -> str:
        """Synchronous version of sheet ID generation"""
        return self.templates["sheet"].format(subject_id=subject_id, version=version)

    async def generate_question_id_async(self, sheet_id: str, question_number: int, db: Session) -> str:
        """
        Generate unique question ID: EXM-2025-JEE_MAIN-001-SUB-PHY-SHT-V01-Q-00028
        """
        try:
            # Validate sheet_id exists
            if not await self._validate_parent_id(db, "question_sheets", "sheet_id", sheet_id):
                raise ValueError(f"Sheet ID {sheet_id} does not exist")

            question_id = self.templates["question"].format(
                sheet_id=sheet_id,
                seq=question_number
            )

            await self._cache_id_mapping("question", question_id, {
                "sheet_id": sheet_id,
                "question_number": question_number
            })

            self.logger.info(
                "Generated question ID",
                question_id=question_id,
                sheet_id=sheet_id,
                question_number=question_number
            )

            return question_id

        except Exception as e:
            self.logger.error("Error generating question ID", error=str(e))
            raise

    def generate_question_id(self, sheet_id: str, question_number: int) -> str:
        """Synchronous version of question ID generation"""
        return self.templates["question"].format(sheet_id=sheet_id, seq=question_number)

    def generate_option_id(self, question_id: str, option_number: int) -> str:
        """
        Generate option ID: EXM-2025-JEE_MAIN-001-SUB-PHY-SHT-V01-Q-00028-OPT-1
        """
        return self.templates["option"].format(
            question_id=question_id,
            number=option_number
        )

    async def generate_asset_id_async(self, parent_id: str, asset_type: str, db: Session) -> str:
        """
        Generate unique asset ID: EXM-2025-JEE_MAIN-001-SUB-PHY-SHT-V01-Q-00028-AST-IMG-001
        """
        try:
            asset_type = asset_type.upper()

            # Get next sequence for this parent and type
            sequence_key = f"ASSET_{parent_id}_{asset_type}"
            next_seq = await self._get_next_sequence_db(db, "ASSET_ID", sequence_key)

            asset_id = self.templates["asset"].format(
                parent_id=parent_id,
                type=asset_type,
                seq=next_seq
            )

            await self._cache_id_mapping("asset", asset_id, {
                "parent_id": parent_id,
                "asset_type": asset_type,
                "sequence": next_seq
            })

            self.logger.info(
                "Generated asset ID",
                asset_id=asset_id,
                parent_id=parent_id,
                asset_type=asset_type,
                sequence=next_seq
            )

            return asset_id

        except Exception as e:
            self.logger.error("Error generating asset ID", error=str(e))
            raise

    def generate_asset_id(self, parent_id: str, asset_type: str) -> str:
        """Synchronous version of asset ID generation"""
        asset_type = asset_type.upper()

        # Simple Redis-based sequence
        redis_key = f"seq:asset:{parent_id}:{asset_type}"
        next_seq = self.redis_client.incr(redis_key)

        return self.templates["asset"].format(
            parent_id=parent_id,
            type=asset_type,
            seq=next_seq
        )

    # Helper Methods
    async def _get_next_sequence_db(self, db: Session, sequence_type: str, sequence_key: str) -> int:
        """Get next sequence number from database"""
        try:
            # Try to get existing sequence
            result = db.execute(
                text("""
                    SELECT current_value FROM id_sequences 
                    WHERE sequence_type = :type AND sequence_key = :key
                """),
                {"type": sequence_type, "key": sequence_key}
            ).fetchone()

            if result:
                # Update existing sequence
                new_value = result[0] + 1
                db.execute(
                    text("""
                        UPDATE id_sequences 
                        SET current_value = :value, updated_at = CURRENT_TIMESTAMP
                        WHERE sequence_type = :type AND sequence_key = :key
                    """),
                    {"value": new_value, "type": sequence_type, "key": sequence_key}
                )
            else:
                # Create new sequence
                new_value = 1
                db.execute(
                    text("""
                        INSERT INTO id_sequences (sequence_type, sequence_key, current_value, prefix, format_template)
                        VALUES (:type, :key, :value, :prefix, :template)
                    """),
                    {
                        "type": sequence_type,
                        "key": sequence_key,
                        "value": new_value,
                        "prefix": sequence_type.split("_")[0],
                        "template": self.templates.get(sequence_type.lower().split("_")[0], "")
                    }
                )

            db.commit()
            return new_value

        except Exception as e:
            db.rollback()
            self.logger.error("Error getting sequence", sequence_type=sequence_type, error=str(e))
            raise

    async def _validate_parent_id(self, db: Session, table: str, column: str, parent_id: str) -> bool:
        """Validate that parent ID exists"""
        try:
            result = db.execute(
                text(f"SELECT 1 FROM {table} WHERE {column} = :id LIMIT 1"),
                {"id": parent_id}
            ).fetchone()

            return result is not None

        except Exception as e:
            self.logger.error("Error validating parent ID", table=table, parent_id=parent_id, error=str(e))
            return False

    async def _cache_id_mapping(self, id_type: str, id_value: str, metadata: Dict) -> None:
        """Cache ID mapping in Redis for fast lookups"""
        try:
            cache_key = f"id_mapping:{id_type}:{id_value}"
            await asyncio.to_thread(
                self.redis_client.hset,
                cache_key,
                mapping=metadata
            )
            await asyncio.to_thread(
                self.redis_client.expire,
                cache_key,
                86400  # 24 hours
            )

        except Exception as e:
            self.logger.warning("Failed to cache ID mapping", id_value=id_value, error=str(e))
            # Don't raise - caching failure shouldn't break ID generation

    def parse_id(self, id_value: str) -> Dict[str, str]:
        """
        Parse hierarchical ID and extract components

        Example: EXM-2025-JEE_MAIN-001-SUB-PHY-SHT-V01-Q-00028
        Returns: {
            "exam_year": "2025",
            "exam_type": "JEE_MAIN",
            "exam_sequence": "001",
            "subject_code": "PHY",
            "sheet_version": "01",
            "question_number": "00028"
        }
        """
        try:
            parts = id_value.split("-")
            parsed = {}

            if len(parts) >= 4 and parts[0] == "EXM":
                parsed["exam_year"] = parts[1]
                parsed["exam_type"] = parts[2]
                parsed["exam_sequence"] = parts[3]

                # Check for subject
                if len(parts) >= 6 and parts[4] == "SUB":
                    parsed["subject_code"] = parts[5]

                    # Check for sheet
                    if len(parts) >= 8 and parts[6] == "SHT":
                        parsed["sheet_version"] = parts[7].replace("V", "")

                        # Check for question
                        if len(parts) >= 10 and parts[8] == "Q":
                            parsed["question_number"] = parts[9]

            return parsed

        except Exception as e:
            self.logger.error("Error parsing ID", id_value=id_value, error=str(e))
            return {}

    def get_parent_id(self, id_value: str) -> Optional[str]:
        """
        Get parent ID from hierarchical ID

        Example: EXM-2025-JEE_MAIN-001-SUB-PHY-SHT-V01-Q-00028
        Returns: EXM-2025-JEE_MAIN-001-SUB-PHY-SHT-V01
        """
        try:
            parts = id_value.split("-")

            # Remove last two parts (type and value)
            if len(parts) >= 2:
                parent_parts = parts[:-2]
                return "-".join(parent_parts)

            return None

        except Exception as e:
            self.logger.error("Error getting parent ID", id_value=id_value, error=str(e))
            return None

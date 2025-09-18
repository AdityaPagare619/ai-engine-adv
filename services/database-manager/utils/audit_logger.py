"""
Audit Logger
Comprehensive audit trail for all system operations
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional
import asyncio

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from config.database import get_redis_client
from config.logging import logger


class AuditLogger:
    """
    Industry-grade audit logging system
    Tracks all administrative and system operations
    """

    def __init__(self):
        self.redis_client = get_redis_client()
        self.logger = logger

    async def log_operation(
            self,
            operation_type: str,
            details: Dict[str, Any],
            user_id: Optional[str] = None,
            session_id: Optional[str] = None
    ) -> str:
        """Log an operation to audit trail"""
        try:
            audit_id = f"audit_{int(datetime.utcnow().timestamp())}"

            audit_entry = {
                "audit_id": audit_id,
                "timestamp": datetime.utcnow().isoformat(),
                "operation_type": operation_type,
                "user_id": user_id or "system",
                "session_id": session_id,
                "details": details,
                "ip_address": None,  # Would be populated from request context
                "user_agent": None  # Would be populated from request context
            }

            # Store in Redis with TTL
            await asyncio.to_thread(
                self.redis_client.setex,
                f"audit:{audit_id}",
                86400 * 30,  # 30 days
                json.dumps(audit_entry)
            )

            # Also log to structured logger
            self.logger.info(
                "Audit log entry created",
                audit_id=audit_id,
                operation_type=operation_type,
                user_id=user_id,
                details=details
            )

            return audit_id

        except Exception as e:
            self.logger.error("Failed to create audit log", error=str(e))
            raise

    async def get_audit_trail(
            self,
            operation_type: Optional[str] = None,
            user_id: Optional[str] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            limit: int = 100
    ) -> list:
        """Retrieve audit trail with filters"""
        try:
            # This is a simplified version - in production you'd use a proper search
            # For now, return recent audit entries from Redis

            pattern = "audit:*"
            keys = await asyncio.to_thread(self.redis_client.keys, pattern)

            audit_entries = []
            for key in keys[:limit]:
                try:
                    data = await asyncio.to_thread(self.redis_client.get, key)
                    if data:
                        entry = json.loads(data)

                        # Apply filters
                        if operation_type and entry.get("operation_type") != operation_type:
                            continue
                        if user_id and entry.get("user_id") != user_id:
                            continue

                        audit_entries.append(entry)

                except Exception:
                    continue

            # Sort by timestamp (newest first)
            audit_entries.sort(
                key=lambda x: x.get("timestamp", ""),
                reverse=True
            )

            return audit_entries[:limit]

        except Exception as e:
            self.logger.error("Failed to retrieve audit trail", error=str(e))
            return []

    def log_sync(
            self,
            operation_type: str,
            details: Dict[str, Any],
            user_id: Optional[str] = None
    ) -> str:
        """Synchronous version of log_operation"""
        try:
            audit_id = f"audit_{int(datetime.utcnow().timestamp())}"

            audit_entry = {
                "audit_id": audit_id,
                "timestamp": datetime.utcnow().isoformat(),
                "operation_type": operation_type,
                "user_id": user_id or "system",
                "details": details
            }

            # Store in Redis
            self.redis_client.setex(
                f"audit:{audit_id}",
                86400 * 30,  # 30 days
                json.dumps(audit_entry)
            )

            # Log
            self.logger.info(
                "Audit log entry created",
                audit_id=audit_id,
                operation_type=operation_type,
                user_id=user_id
            )

            return audit_id

        except Exception as e:
            self.logger.error("Failed to create audit log", error=str(e))
            return ""

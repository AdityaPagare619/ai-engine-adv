from __future__ import annotations
import os
import logging
import time
from typing import Any
from supabase import create_client, Client
from postgrest.exceptions import APIError
try:
    from dotenv import load_dotenv, find_dotenv  # type: ignore
except Exception:
    def load_dotenv(*args, **kwargs):  # type: ignore
        return False
    def find_dotenv(*args, **kwargs):  # type: ignore
        return ""

logger = logging.getLogger("supabase_client")


class SupabaseClient:
    """
    Lightweight but robust Supabase client wrapper.
    - Auto-configures from .env files or environment variables (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY).
    - Provides health check.
    - Returns wrapped table objects with retry/error handling.
    """

    def __init__(self, url: str | None = None, key: str | None = None):
        # Load .env files if present (ai_engine/.env then project .env)
        try:
            # Attempt to load ai_engine/.env explicitly first
            ai_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                       ".env")
            if os.path.exists(ai_env_path):
                load_dotenv(ai_env_path, override=False)
            # Then load project root .env if found
            env_file = find_dotenv(usecwd=True)
            if env_file:
                load_dotenv(env_file, override=False)
        except Exception:
            # Do not fail if dotenv isn't available or files absent
            pass

        self.url = url or os.getenv("SUPABASE_URL")
        self.key = key or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not self.url or not self.key:
            raise RuntimeError(
                "Supabase URL/Service Role Key not configured. Set SUPABASE_URL and "
                "SUPABASE_SERVICE_ROLE_KEY in ai_engine/.env or project .env, or pass them explicitly."
            )

        try:
            self.client: Client = create_client(self.url, self.key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise

    def table(self, name: str) -> "SupabaseTableWrapper":
        """Return a wrapped table reference with safe error handling."""
        try:
            return SupabaseTableWrapper(self.client.table(name), name)
        except Exception as e:
            logger.error(f"Failed to get table reference for {name}: {e}")
            raise

    def health_check(self) -> bool:
        """Check if Supabase connection is healthy by probing a known table."""
        try:
            self.client.table("bkt_parameters").select("concept_id").limit(1).execute()
            return True
        except Exception as e:
            logger.warning(f"Supabase health check failed: {e}")
            return False


class SupabaseTableWrapper:
    """Wrapper for Supabase table operations with enhanced error handling."""

    def __init__(self, table: Any, table_name: str):
        self.table = table
        self.table_name = table_name

    def select(self, *args, **kwargs) -> "SupabaseQueryWrapper":
        return SupabaseQueryWrapper(self.table.select(*args, **kwargs), self.table_name, "select")

    def insert(self, data, **kwargs) -> "SupabaseQueryWrapper":
        return SupabaseQueryWrapper(self.table.insert(data, **kwargs), self.table_name, "insert")

    def upsert(self, data, **kwargs) -> "SupabaseQueryWrapper":
        return SupabaseQueryWrapper(self.table.upsert(data, **kwargs), self.table_name, "upsert")

    def update(self, data, **kwargs) -> "SupabaseQueryWrapper":
        return SupabaseQueryWrapper(self.table.update(data, **kwargs), self.table_name, "update")

    def delete(self, **kwargs) -> "SupabaseQueryWrapper":
        return SupabaseQueryWrapper(self.table.delete(**kwargs), self.table_name, "delete")


class SupabaseQueryWrapper:
    """
    Wrapper for Supabase query operations with:
    - Retry logic
    - Enhanced error handling
    - Operation logging
    """

    def __init__(self, query: Any, table_name: str, operation: str):
        self.query = query
        self.table_name = table_name
        self.operation = operation

    def eq(self, column: str, value: Any) -> "SupabaseQueryWrapper":
        return SupabaseQueryWrapper(self.query.eq(column, value), self.table_name, self.operation)

    def neq(self, column: str, value: Any) -> "SupabaseQueryWrapper":
        return SupabaseQueryWrapper(self.query.neq(column, value), self.table_name, self.operation)

    def in_(self, column: str, values: list) -> "SupabaseQueryWrapper":
        return SupabaseQueryWrapper(self.query.in_(column, values), self.table_name, self.operation)

    def order(self, column: str, **kwargs) -> "SupabaseQueryWrapper":
        return SupabaseQueryWrapper(self.query.order(column, **kwargs), self.table_name, self.operation)

    def limit(self, count: int) -> "SupabaseQueryWrapper":
        return SupabaseQueryWrapper(self.query.limit(count), self.table_name, self.operation)

    def single(self) -> "SupabaseQueryWrapper":
        return SupabaseQueryWrapper(self.query.single(), self.table_name, self.operation)

    def execute(self, max_retries: int = 3):
        """Execute the query with retry logic and error handling."""
        last_exception = None

        for attempt in range(max_retries):
            try:
                result = self.query.execute()

                # Log successful writes
                if self.operation in ['insert', 'update', 'upsert', 'delete']:
                    logger.info(f"Successfully executed {self.operation} on {self.table_name}")

                return result

            except APIError as e:
                last_exception = e
                logger.warning(
                    f"API error on {self.operation} for {self.table_name} "
                    f"(attempt {attempt + 1}/{max_retries}): {e}"
                )

                # Constraint violations → no retry
                if getattr(e, "code", None) in ['23505', '23503']:
                    logger.error(f"Database constraint violation on {self.table_name}: {e}")
                    break

            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Error on {self.operation} for {self.table_name} "
                    f"(attempt {attempt + 1}/{max_retries}): {e}"
                )

            # Exponential backoff
            if attempt < max_retries - 1:
                time.sleep(0.5 * (2 ** attempt))

        # All retries failed
        logger.error(
            f"All retries failed for {self.operation} on {self.table_name}: {last_exception}"
        )
        raise last_exception

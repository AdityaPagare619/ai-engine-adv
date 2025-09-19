import os
import logging
from typing import Optional
from supabase import create_client, Client
from postgrest.exceptions import APIError

logger = logging.getLogger("supabase_client")

class SupabaseClient:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.url or not self.key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set. "
                "Check your environment configuration."
            )
        
        try:
            self.client: Client = create_client(self.url, self.key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    def table(self, name: str):
        """Get a table reference with error handling wrapper."""
        try:
            return SupabaseTableWrapper(self.client.table(name), name)
        except Exception as e:
            logger.error(f"Failed to get table reference for {name}: {e}")
            raise
    
    def health_check(self) -> bool:
        """Check if Supabase connection is healthy."""
        try:
            # Simple query to test connection
            result = self.client.table("bkt_parameters").select("concept_id").limit(1).execute()
            return True
        except Exception as e:
            logger.warning(f"Supabase health check failed: {e}")
            return False

class SupabaseTableWrapper:
    """Wrapper for Supabase table operations with enhanced error handling."""
    
    def __init__(self, table, table_name: str):
        self.table = table
        self.table_name = table_name
    
    def select(self, *args, **kwargs):
        return SupabaseQueryWrapper(self.table.select(*args, **kwargs), self.table_name, "select")
    
    def insert(self, data, **kwargs):
        return SupabaseQueryWrapper(self.table.insert(data, **kwargs), self.table_name, "insert")
    
    def upsert(self, data, **kwargs):
        return SupabaseQueryWrapper(self.table.upsert(data, **kwargs), self.table_name, "upsert")
    
    def update(self, data, **kwargs):
        return SupabaseQueryWrapper(self.table.update(data, **kwargs), self.table_name, "update")
    
    def delete(self, **kwargs):
        return SupabaseQueryWrapper(self.table.delete(**kwargs), self.table_name, "delete")

class SupabaseQueryWrapper:
    """Wrapper for Supabase query operations with enhanced error handling and retries."""
    
    def __init__(self, query, table_name: str, operation: str):
        self.query = query
        self.table_name = table_name
        self.operation = operation
    
    def eq(self, column: str, value):
        return SupabaseQueryWrapper(self.query.eq(column, value), self.table_name, self.operation)
    
    def neq(self, column: str, value):
        return SupabaseQueryWrapper(self.query.neq(column, value), self.table_name, self.operation)
    
    def in_(self, column: str, values):
        return SupabaseQueryWrapper(self.query.in_(column, values), self.table_name, self.operation)
    
    def order(self, column: str, **kwargs):
        return SupabaseQueryWrapper(self.query.order(column, **kwargs), self.table_name, self.operation)
    
    def limit(self, count: int):
        return SupabaseQueryWrapper(self.query.limit(count), self.table_name, self.operation)
    
    def single(self):
        return SupabaseQueryWrapper(self.query.single(), self.table_name, self.operation)
    
    def execute(self, max_retries: int = 3):
        """Execute the query with retry logic and enhanced error handling."""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                result = self.query.execute()
                
                # Log successful operations for audit trail
                if self.operation in ['insert', 'update', 'upsert', 'delete']:
                    logger.info(f"Successfully executed {self.operation} on {self.table_name}")
                
                return result
                
            except APIError as e:
                last_exception = e
                logger.warning(f"API error on {self.operation} for {self.table_name} (attempt {attempt + 1}/{max_retries}): {e}")
                
                # Don't retry on certain errors
                if e.code in ['23505', '23503']:  # Unique violation, foreign key violation
                    logger.error(f"Database constraint violation on {self.table_name}: {e}")
                    break
                    
            except Exception as e:
                last_exception = e
                logger.warning(f"Error on {self.operation} for {self.table_name} (attempt {attempt + 1}/{max_retries}): {e}")
            
            # Brief delay before retry (exponential backoff)
            if attempt < max_retries - 1:
                import time
                time.sleep(0.5 * (2 ** attempt))
        
        # All retries failed
        logger.error(f"All retries failed for {self.operation} on {self.table_name}: {last_exception}")
        raise last_exception

"""
Advanced Database Connection Pool Manager
High-performance connection pooling with health monitoring
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from sqlalchemy import text, create_engine
from sqlalchemy.pool import QueuePool
import asyncpg
import structlog

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from config.database import engine, async_pool, create_async_pool
from config.environment import settings
from config.logging import logger


class DatabasePool:
    """
    Advanced database connection pool with monitoring and optimization
    """

    def __init__(self):
        self.logger = logger
        self.engine = engine
        self.pool_stats = {
            "connections_created": 0,
            "connections_closed": 0,
            "active_connections": 0,
            "pool_hits": 0,
            "pool_misses": 0,
            "last_health_check": None
        }

    async def check_health(self) -> Dict[str, Any]:
        """Comprehensive health check of database connections"""
        try:
            start_time = time.time()

            # Test synchronous connection
            with self.engine.connect() as conn:
                sync_result = conn.execute(text("SELECT 1 as test")).fetchone()
                sync_latency = time.time() - start_time

            # Test async connection
            async_start = time.time()
            pool = await create_async_pool()
            async with pool.acquire() as conn:
                async_result = await conn.fetchval("SELECT 1")
                async_latency = time.time() - async_start

            # Get pool statistics
            pool_info = self.engine.pool.status()

            health_status = {
                "status": "healthy",
                "sync_connection": {
                    "success": sync_result[0] == 1,
                    "latency_ms": round(sync_latency * 1000, 2)
                },
                "async_connection": {
                    "success": async_result == 1,
                    "latency_ms": round(async_latency * 1000, 2)
                },
                "pool_info": {
                    "size": self.engine.pool.size(),
                    "checked_in": self.engine.pool.checkedin(),
                    "checked_out": self.engine.pool.checkedout(),
                    "overflow": self.engine.pool.overflow(),
                    "invalid": self.engine.pool.invalid()
                },
                "performance": self.pool_stats
            }

            self.pool_stats["last_health_check"] = time.time()

            self.logger.info(
                "Database health check completed",
                sync_latency=sync_latency,
                async_latency=async_latency,
                pool_size=health_status["pool_info"]["size"]
            )

            return health_status

        except Exception as e:
            self.logger.error("Database health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def get_database_statistics(self, db) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        try:
            # Table sizes and row counts
            table_stats = await self._get_table_statistics(db)

            # Index usage statistics
            index_stats = await self._get_index_statistics(db)

            # Connection statistics
            connection_stats = await self._get_connection_statistics(db)

            # Query performance statistics
            query_stats = await self._get_query_statistics(db)

            statistics = {
                "tables": table_stats,
                "indexes": index_stats,
                "connections": connection_stats,
                "queries": query_stats,
                "pool_statistics": self.pool_stats,
                "timestamp": time.time()
            }

            return statistics

        except Exception as e:
            self.logger.error("Error retrieving database statistics", error=str(e))
            raise

    async def _get_table_statistics(self, db) -> List[Dict[str, Any]]:
        """Get table size and row count statistics"""
        try:
            query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation
                FROM pg_stats 
                WHERE schemaname = 'public'
                ORDER BY tablename, attname;
            """)

            result = db.execute(query).fetchall()

            # Group by table
            tables = {}
            for row in result:
                table_name = row[1]
                if table_name not in tables:
                    tables[table_name] = {
                        "name": table_name,
                        "schema": row[0],
                        "columns": []
                    }

                tables[table_name]["columns"].append({
                    "name": row[2],
                    "distinct_values": row[3],
                    "correlation": row[4]
                })

            return list(tables.values())

        except Exception as e:
            self.logger.error("Error getting table statistics", error=str(e))
            return []

    async def _get_index_statistics(self, db) -> List[Dict[str, Any]]:
        """Get index usage statistics"""
        try:
            query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes 
                WHERE schemaname = 'public'
                ORDER BY idx_tup_read DESC;
            """)

            result = db.execute(query).fetchall()

            indexes = []
            for row in result:
                indexes.append({
                    "schema": row[0],
                    "table": row[1],
                    "name": row[2],
                    "tuples_read": row[3],
                    "tuples_fetched": row[4],
                    "efficiency": round((row[4] / max(row[3], 1)) * 100, 2)
                })

            return indexes

        except Exception as e:
            self.logger.error("Error getting index statistics", error=str(e))
            return []

    async def _get_connection_statistics(self, db) -> Dict[str, Any]:
        """Get connection statistics"""
        try:
            query = text("""
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections
                FROM pg_stat_activity;
            """)

            result = db.execute(query).fetchone()

            return {
                "total": result[0],
                "active": result[1],
                "idle": result[2]
            }

        except Exception as e:
            self.logger.error("Error getting connection statistics", error=str(e))
            return {}

    async def _get_query_statistics(self, db) -> Dict[str, Any]:
        """Get query performance statistics"""
        try:
            # This requires pg_stat_statements extension
            query = text("""
                SELECT 
                    calls,
                    total_time,
                    mean_time,
                    stddev_time,
                    rows
                FROM pg_stat_statements 
                WHERE query LIKE '%exam_registry%' OR query LIKE '%questions%'
                ORDER BY total_time DESC 
                LIMIT 10;
            """)

            try:
                result = db.execute(query).fetchall()

                queries = []
                for row in result:
                    queries.append({
                        "calls": row[0],
                        "total_time": row[1],
                        "mean_time": round(row[2], 2),
                        "stddev_time": round(row[3], 2) if row[3] else 0,
                        "rows": row[4]
                    })

                return {"top_queries": queries}

            except Exception:
                # pg_stat_statements not available
                return {"top_queries": [], "note": "pg_stat_statements extension not available"}

        except Exception as e:
            self.logger.error("Error getting query statistics", error=str(e))
            return {}

    async def run_cleanup(self) -> Dict[str, Any]:
        """Run database cleanup operations"""
        try:
            cleanup_results = {}

            # Clean up old import operations (older than 30 days)
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    DELETE FROM import_operations 
                    WHERE created_at < CURRENT_DATE - INTERVAL '30 days'
                    AND status IN ('COMPLETED', 'FAILED');
                """))
                cleanup_results["old_import_operations"] = result.rowcount

                # Clean up orphaned sequences
                result = conn.execute(text("""
                    DELETE FROM id_sequences 
                    WHERE updated_at < CURRENT_DATE - INTERVAL '90 days'
                    AND sequence_type NOT IN ('EXAM_ID', 'SUBJECT_ID');
                """))
                cleanup_results["orphaned_sequences"] = result.rowcount

                # Update table statistics
                conn.execute(text("ANALYZE;"))
                cleanup_results["statistics_updated"] = True

                conn.commit()

            self.logger.info(
                "Database cleanup completed",
                results=cleanup_results
            )

            return cleanup_results

        except Exception as e:
            self.logger.error("Database cleanup failed", error=str(e))
            raise

    async def optimize_performance(self) -> Dict[str, Any]:
        """Run performance optimization tasks"""
        try:
            optimization_results = {}

            with self.engine.connect() as conn:
                # Vacuum analyze critical tables
                critical_tables = [
                    'exam_registry', 'subject_registry', 'questions',
                    'question_options', 'question_assets'
                ]

                for table in critical_tables:
                    conn.execute(text(f"VACUUM ANALYZE {table};"))

                optimization_results["tables_optimized"] = len(critical_tables)

                # Reindex if needed
                conn.execute(text("REINDEX INDEX CONCURRENTLY IF EXISTS idx_questions_question_id;"))
                optimization_results["indexes_rebuilt"] = 1

                conn.commit()

            self.logger.info(
                "Performance optimization completed",
                results=optimization_results
            )

            return optimization_results

        except Exception as e:
            self.logger.error("Performance optimization failed", error=str(e))
            raise

    def get_pool_status(self) -> Dict[str, Any]:
        """Get current pool status"""
        return {
            "size": self.engine.pool.size(),
            "checked_in": self.engine.pool.checkedin(),
            "checked_out": self.engine.pool.checkedout(),
            "overflow": self.engine.pool.overflow(),
            "invalid": self.engine.pool.invalid(),
            "statistics": self.pool_stats
        }

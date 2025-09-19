"""
Mock Supabase client for local testing without external dependencies.
This allows us to test the BKT integration without requiring actual Supabase setup.
"""

import json
from typing import Dict, List, Any, Optional
from unittest.mock import MagicMock


class MockSupabaseTable:
    def __init__(self, table_name: str, data_store: Dict[str, List[Dict]]):
        self.table_name = table_name
        self.data_store = data_store
        self._query = {}
        self._select_fields = "*"
        
    def select(self, fields: str):
        self._select_fields = fields
        return self
        
    def eq(self, field: str, value: Any):
        self._query[field] = value
        return self
        
    def single(self):
        self._is_single = True
        return self
        
    def execute(self):
        # Mock execute behavior
        table_data = self.data_store.get(self.table_name, [])
        
        # Filter by query
        filtered_data = []
        for row in table_data:
            match = True
            for field, value in self._query.items():
                if row.get(field) != value:
                    match = False
                    break
            if match:
                filtered_data.append(row)
        
        # Return mock response
        result = MagicMock()
        if hasattr(self, '_is_single'):
            result.data = filtered_data[0] if filtered_data else None
        else:
            result.data = filtered_data
        return result
    
    def upsert(self, data: Dict[str, Any]):
        # Mock upsert - add or update data
        table_data = self.data_store.setdefault(self.table_name, [])
        
        # Simple upsert logic - replace if exists, add if not
        existing_index = None
        primary_key = self._get_primary_key(data)
        
        if primary_key:
            for i, row in enumerate(table_data):
                if self._matches_primary_key(row, data, primary_key):
                    existing_index = i
                    break
        
        if existing_index is not None:
            table_data[existing_index] = data
        else:
            table_data.append(data)
        
        return self
    
    def insert(self, data: Dict[str, Any]):
        table_data = self.data_store.setdefault(self.table_name, [])
        table_data.append(data)
        return self
    
    def _get_primary_key(self, data: Dict[str, Any]) -> Optional[str]:
        # Determine primary key based on table
        pk_map = {
            "bkt_parameters": "concept_id",
            "bkt_knowledge_states": ["student_id", "concept_id"],
            "question_metadata_cache": "question_id",
            "bkt_update_logs": None  # No primary key, always insert
        }
        return pk_map.get(self.table_name)
    
    def _matches_primary_key(self, row: Dict, data: Dict, pk) -> bool:
        if isinstance(pk, list):
            return all(row.get(key) == data.get(key) for key in pk)
        else:
            return row.get(pk) == data.get(pk)


class MockSupabaseClient:
    def __init__(self):
        # In-memory data store
        self.data_store = {
            "bkt_parameters": [
                {
                    "concept_id": "test_concept",
                    "learn_rate": 0.3,
                    "slip_rate": 0.1,
                    "guess_rate": 0.2
                },
                {
                    "concept_id": "kinematics_basic",
                    "learn_rate": 0.3,
                    "slip_rate": 0.1,
                    "guess_rate": 0.2
                }
            ],
            "question_metadata_cache": [
                {
                    "question_id": "PHY_MECH_0001",
                    "difficulty_calibrated": 1.2,
                    "bloom_level": "Apply",
                    "estimated_time_seconds": 120,
                    "required_process_skills": ["kinematics", "problem_solving"]
                },
                {
                    "question_id": "MATH_CALC_0001",
                    "difficulty_calibrated": 0.8,
                    "bloom_level": "Understand",
                    "estimated_time_seconds": 90,
                    "required_process_skills": ["algebra", "differentiation"]
                }
            ],
            "bkt_knowledge_states": [],
            "bkt_update_logs": []
        }
    
    def table(self, table_name: str) -> MockSupabaseTable:
        return MockSupabaseTable(table_name, self.data_store)
    
    def reset_data(self):
        """Reset to clean state for testing"""
        self.data_store["bkt_knowledge_states"] = []
        self.data_store["bkt_update_logs"] = []
    
    def get_data(self, table_name: str) -> List[Dict]:
        """Get current data for debugging"""
        return self.data_store.get(table_name, [])
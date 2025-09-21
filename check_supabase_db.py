#!/usr/bin/env python3
"""
Check Supabase Database Structure and Compare with Documentation
"""
import os
from typing import Dict, List, Any
from datetime import datetime

# Load environment variables
SUPABASE_URL = "https://qxfzjngtmsofegmkgswo.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF4Znpqbmd0bXNvZmVnbWtnc3dvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1ODIxNzU0OSwiZXhwIjoyMDczNzkzNTQ5fQ.CkbBGBf60UjRxTk06E2s6cKcZqvYlk7FL7VVKi2owA8"

def check_supabase_structure():
    """Check Supabase database structure"""
    
    print("🔍 Checking Supabase Database Structure...")
    print("=" * 60)
    
    # Expected tables from documentation
    expected_tables = {
        "bkt_parameters": {
            "purpose": "Stores learning parameters for each concept",
            "key_columns": ["concept_id", "learn_rate", "slip_rate", "guess_rate"]
        },
        "bkt_knowledge_states": {
            "purpose": "Tracks student mastery for each concept", 
            "key_columns": ["student_id", "concept_id", "mastery_probability", "practice_count"]
        },
        "bkt_update_logs": {
            "purpose": "Logs all BKT parameter updates for analytics",
            "key_columns": ["student_id", "concept_id", "previous_mastery", "new_mastery", "is_correct"]
        },
        "question_metadata_cache": {
            "purpose": "Caches question metadata for fast access",
            "key_columns": ["question_id", "subject", "topic", "difficulty_calibrated", "estimated_time_seconds"]
        },
        "bkt_evaluation_windows": {
            "purpose": "Tracks learning progress over time windows",
            "key_columns": ["student_id", "concept_id", "window_start", "window_end", "mastery_gain"]
        },
        "bkt_selection_feedback": {
            "purpose": "Tracks question selection algorithm performance",
            "key_columns": ["student_id", "question_id", "predicted_mastery", "actual_outcome"]
        }
    }
    
    try:
        # Try to import supabase
        try:
            from supabase import create_client
            print("✅ Supabase client library found")
        except ImportError:
            print("❌ Supabase client library not installed")
            print("   Run: pip install supabase")
            return
            
        # Connect to Supabase
        try:
            client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
            print("✅ Successfully connected to Supabase")
        except Exception as e:
            print(f"❌ Failed to connect to Supabase: {e}")
            return
            
        # Check each expected table
        existing_tables = {}
        missing_tables = []
        
        for table_name, table_info in expected_tables.items():
            try:
                # Try to query the table structure (just count rows)
                result = client.table(table_name).select("*").limit(1).execute()
                existing_tables[table_name] = {
                    "exists": True,
                    "row_count": len(result.data),
                    "structure": "accessible"
                }
                print(f"✅ Table '{table_name}' exists and accessible")
                
                # Try to get a sample to understand structure
                if result.data:
                    sample_row = result.data[0]
                    existing_tables[table_name]["sample_columns"] = list(sample_row.keys())
                    
            except Exception as e:
                existing_tables[table_name] = {
                    "exists": False,
                    "error": str(e)
                }
                missing_tables.append(table_name)
                print(f"❌ Table '{table_name}' missing or inaccessible: {e}")
                
        # Generate report
        print("\n📊 DATABASE STRUCTURE ANALYSIS")
        print("=" * 60)
        
        total_tables = len(expected_tables)
        existing_count = len([t for t in existing_tables.values() if t.get("exists", False)])
        
        print(f"Total Expected Tables: {total_tables}")
        print(f"Existing Tables: {existing_count}")
        print(f"Missing Tables: {len(missing_tables)}")
        print(f"Database Completeness: {existing_count/total_tables:.2%}")
        
        if missing_tables:
            print(f"\n🚨 MISSING TABLES:")
            for table in missing_tables:
                print(f"- {table}: {expected_tables[table]['purpose']}")
                
        print(f"\n📋 TABLE DETAILS:")
        for table_name, info in existing_tables.items():
            status = "✅" if info.get("exists", False) else "❌"
            print(f"{status} {table_name}")
            if info.get("exists", False):
                sample_cols = info.get("sample_columns", [])
                if sample_cols:
                    print(f"   Columns found: {', '.join(sample_cols)}")
                    
        # Test basic functionality
        print(f"\n🧪 TESTING BASIC FUNCTIONALITY:")
        
        # Test BKT parameters if table exists
        if existing_tables.get("bkt_parameters", {}).get("exists", False):
            try:
                result = client.table("bkt_parameters").select("*").limit(5).execute()
                print(f"✅ BKT Parameters: {len(result.data)} sample records")
            except Exception as e:
                print(f"❌ BKT Parameters query failed: {e}")
                
        # Test question metadata cache if table exists  
        if existing_tables.get("question_metadata_cache", {}).get("exists", False):
            try:
                result = client.table("question_metadata_cache").select("*").limit(5).execute()
                print(f"✅ Question Metadata Cache: {len(result.data)} sample records")
            except Exception as e:
                print(f"❌ Question Metadata Cache query failed: {e}")
                
        # Generate documentation compliance report
        print(f"\n📄 DOCUMENTATION COMPLIANCE:")
        doc_score = existing_count / total_tables
        if doc_score >= 0.9:
            print("✅ EXCELLENT: Database structure matches documentation")
        elif doc_score >= 0.7:
            print("👍 GOOD: Most tables implemented, minor gaps")
        elif doc_score >= 0.5:
            print("⚠️ PARTIAL: Significant gaps in database structure")
        else:
            print("❌ POOR: Major database structure problems")
            
        return {
            "total_expected": total_tables,
            "existing_count": existing_count,
            "missing_count": len(missing_tables),
            "completeness_score": doc_score,
            "status": "EXCELLENT" if doc_score >= 0.9 else "GOOD" if doc_score >= 0.7 else "PARTIAL" if doc_score >= 0.5 else "POOR",
            "existing_tables": existing_tables,
            "missing_tables": missing_tables
        }
        
    except Exception as e:
        print(f"💥 Critical error during database check: {e}")
        return None

def main():
    """Main function"""
    print("🗄️ JEE Smart AI Platform - Supabase Database Analysis")
    print("=" * 80)
    
    result = check_supabase_structure()
    
    if result:
        print(f"\n🎯 FINAL ASSESSMENT:")
        print(f"Database Status: {result['status']}")
        print(f"Completeness: {result['completeness_score']:.2%}")
        
        if result['missing_tables']:
            print(f"\n💡 RECOMMENDATIONS:")
            print("- Run the supabase_tables.sql script to create missing tables")
            print("- Verify Supabase connection permissions")
            print("- Check table Row Level Security (RLS) policies")
    else:
        print("\n🚨 Unable to complete database analysis")

if __name__ == "__main__":
    main()
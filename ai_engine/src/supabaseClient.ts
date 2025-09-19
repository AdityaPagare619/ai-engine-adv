import { Pool } from 'pg';
import dotenv from 'dotenv';
dotenv.config();

// PostgreSQL connection pool
export const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: false,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Supabase-compatible interface for existing code
export const supabase = {
  rpc: async (functionName: string, params: any = {}) => {
    const client = await pool.connect();
    try {
      let result;
      
      // Handle different function signatures
      if (functionName === 'update_knowledge_state_bkt') {
        result = await client.query(
          `SELECT ${functionName}($1, $2, $3, $4) as result`,
          [params.p_student_id, params.p_concept_id, params.p_is_correct, params.p_response_time_ms]
        );
        return { data: result.rows[0]?.result, error: null };
      } else if (functionName === 'recommend_questions_linucb') {
        result = await client.query(
          `SELECT ${functionName}($1, $2, $3) as result`,
          [params.p_student_id, params.p_context || '{}', params.p_limit || 10]
        );
        return { data: result.rows[0]?.result, error: null };
      } else if (functionName === 'predict_exam_score') {
        result = await client.query(
          `SELECT ${functionName}($1, $2) as result`,
          [params.p_student_id, params.p_features || '{}']
        );
        return { data: result.rows[0]?.result, error: null };
      } else if (functionName === 'write_recommendation_log') {
        result = await client.query(
          `SELECT ${functionName}($1, $2) as result`,
          [params.p_student_id, params.p_payload]
        );
        return { data: result.rows[0]?.result, error: null };
      } else if (functionName === 'write_prediction_log') {
        result = await client.query(
          `SELECT ${functionName}($1, $2) as result`,
          [params.p_student_id, params.p_payload]
        );
        return { data: result.rows[0]?.result, error: null };
      } else {
        // Generic fallback
        result = await client.query(`SELECT ${functionName}($1) as result`, [params]);
        return { data: result.rows[0]?.result, error: null };
      }
    } catch (error) {
      console.error(`RPC Error for ${functionName}:`, error.message);
      return { data: null, error };
    } finally {
      client.release();
    }
  },
  from: (table: string) => {
    return {
      select: async (columns = '*') => {
        const client = await pool.connect();
        try {
          const result = await client.query(`SELECT ${columns} FROM ${table}`);
          return { data: result.rows, error: null };
        } catch (error) {
          return { data: null, error };
        } finally {
          client.release();
        }
      },
      insert: async (data: any) => {
        const client = await pool.connect();
        try {
          const columns = Object.keys(data).join(', ');
          const values = Object.values(data);
          const placeholders = values.map((_, i) => `$${i + 1}`).join(', ');
          const result = await client.query(
            `INSERT INTO ${table} (${columns}) VALUES (${placeholders}) RETURNING *`,
            values
          );
          return { data: result.rows, error: null };
        } catch (error) {
          return { data: null, error };
        } finally {
          client.release();
        }
      }
    };
  }
};

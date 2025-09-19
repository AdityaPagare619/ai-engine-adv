// Types based on the database schema
export interface StudentProfile {
  id: string;
  auth_user_id?: string;
  student_id: string;
  email: string;
  full_name: string;
  grade_level: 11 | 12 | 13;
  target_exam: 'JEE_MAIN' | 'JEE_ADV' | 'NEET';
  exam_date?: Date;
  phone_number?: string;
  parent_email?: string;
  ai_consent_given: boolean;
  ai_consent_timestamp?: Date;
  data_retention_days: number;
  onboarding_completed: boolean;
  last_active_at?: Date;
  timezone: string;
  device_info: Record<string, any>;
  created_at: Date;
  updated_at: Date;
  metadata: Record<string, any>;
}

export interface KnowledgeConcept {
  id: string;
  concept_code: string;
  concept_name: string;
  subject: string;
  chapter?: string;
  topic?: string;
  subtopic?: string;
  difficulty_level: number;
  bloom_taxonomy: 'remember' | 'understand' | 'apply' | 'analyze' | 'evaluate' | 'create';
  prerequisite_concepts: string[];
  parent_concept_id?: string;
  concept_depth: number;
  is_leaf_concept: boolean;
  estimated_learning_time_minutes?: number;
  concept_metadata: Record<string, any>;
  created_at: Date;
  updated_at: Date;
}

export interface StudentKnowledgeState {
  id: string;
  student_id: string;
  concept_id: string;
  mastery_probability: number;
  confidence_interval: number;
  learning_rate: number;
  forgetting_rate: number;
  slip_probability: number;
  guess_probability: number;
  practice_count: number;
  correct_count: number;
  total_time_spent_seconds: number;
  first_encounter_at?: Date;
  last_practice_at?: Date;
  last_correct_at?: Date;
  last_incorrect_at?: Date;
  misconceptions: any[];
  learning_curve_params: Record<string, any>;
  attention_patterns: Record<string, any>;
  updated_at: Date;
}

export interface LearningSession {
  id: string;
  student_id: string;
  session_type: 'drill' | 'mock' | 'revision' | 'diagnostic' | 'practice';
  started_at: Date;
  ended_at?: Date;
  planned_duration_minutes?: number;
  actual_duration_minutes?: number;
  subject_focus?: string;
  topics_covered: string[];
  difficulty_target?: number;
  total_questions: number;
  correct_answers: number;
  skipped_questions: number;
  time_per_question_avg?: number;
  device_info: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  browser_fingerprint?: string;
  ai_model_version?: string;
  recommendation_strategy?: string;
  adaptive_parameters: Record<string, any>;
  session_quality_score?: number;
  interruption_count: number;
  focus_loss_events: number;
  session_metadata: Record<string, any>;
  created_at: Date;
}

export interface QuestionInteraction {
  id: string;
  session_id: string;
  student_id: string;
  question_id: string;
  question_external_id?: string;
  interaction_sequence: number;
  question_shown_at: Date;
  first_interaction_at?: Date;
  first_response_at?: Date;
  final_response_at?: Date;
  time_spent_milliseconds?: number;
  time_to_first_response_ms?: number;
  selected_option?: number;
  response_confidence?: number;
  is_correct?: boolean;
  correct_option?: number;
  answer_changes: number;
  revisit_count: number;
  hint_requests: number;
  help_seeking_events: number;
  keystroke_patterns: any[];
  mouse_movement_patterns: any[];
  scroll_behavior: any[];
  focus_events: any[];
  diagram_interactions: any[];
  text_selection_events: any[];
  formula_interaction_events: any[];
  predicted_correctness?: number;
  predicted_difficulty?: number;
  knowledge_state_before?: Record<string, any>;
  knowledge_state_after?: Record<string, any>;
  interaction_quality_flags: any[];
  data_completeness_score: number;
  interaction_metadata: Record<string, any>;
  created_at: Date;
}

export interface AIRecommendation {
  id: string;
  student_id: string;
  session_id?: string;
  recommendation_type: string;
  context_state: Record<string, any>;
  recommended_questions: string[];
  recommended_topics: string[];
  recommended_difficulty_range?: any;
  algorithm_name: string;
  algorithm_version: string;
  model_parameters: Record<string, any>;
  confidence_score?: number;
  expected_learning_gain?: number;
  diversity_score?: number;
  novelty_score?: number;
  recommendation_shown: boolean;
  recommendation_followed: boolean;
  actual_performance?: number;
  recommendation_effectiveness?: number;
  experiment_group?: string;
  control_group_flag: boolean;
  created_at: Date;
  expires_at: Date;
}

export interface AIPrediction {
  id: string;
  student_id: string;
  prediction_type: string;
  prediction_horizon_days: number;
  prediction_confidence?: number;
  predicted_score?: number;
  score_confidence_interval?: Record<string, any>;
  predicted_percentile?: number;
  subject_wise_predictions: Record<string, any>;
  concept_mastery_timeline: Record<string, any>;
  improvement_trajectory: Record<string, any>;
  dropout_risk_score?: number;
  attention_deficit_risk?: number;
  burnout_risk_score?: number;
  model_name: string;
  model_version: string;
  ensemble_components: any[];
  feature_importance: Record<string, any>;
  prediction_accuracy?: number;
  calibration_error?: number;
  prediction_context: Record<string, any>;
  created_at: Date;
  validated_at?: Date;
}

export interface BKTUpdateParams {
  studentId: string;
  conceptId: string;
  isCorrect: boolean;
  responseTimeMs?: number;
}

export interface BKTUpdateResult {
  previous_mastery: number;
  new_mastery: number;
  learning_occurred: boolean;
  confidence_change: number;
}

export interface RecommendationRequest {
  studentId: string;
  contextState: Record<string, any>;
  sessionId?: string;
  recommendationType?: string;
  maxRecommendations?: number;
}

export interface PredictionRequest {
  studentId: string;
  predictionType: string;
  horizonDays: number;
}

// API Response types
export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: Date;
}

// Database query result types
export interface QueryResult<T = any> {
  data: T | null;
  error: Error | null;
}
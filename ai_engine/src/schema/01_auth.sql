-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Student profiles (extends Supabase auth.users)
CREATE TABLE public.student_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    student_id VARCHAR(50) UNIQUE NOT NULL, -- External student ID
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    grade_level INTEGER CHECK (grade_level IN (11, 12, 13)), -- 11th, 12th, Repeater
    target_exam VARCHAR(20) CHECK (target_exam IN ('JEE_MAIN', 'JEE_ADV', 'NEET')),
    exam_date DATE,
    phone_number VARCHAR(15),
    parent_email VARCHAR(255),

    -- AI Engine specific fields
    ai_consent_given BOOLEAN DEFAULT FALSE,
    ai_consent_timestamp TIMESTAMPTZ,
    data_retention_days INTEGER DEFAULT 365,

    -- Metadata and tracking
    onboarding_completed BOOLEAN DEFAULT FALSE,
    last_active_at TIMESTAMPTZ,
    timezone VARCHAR(50) DEFAULT 'Asia/Kolkata',
    device_info JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Ensure data integrity
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Student preferences and settings
CREATE TABLE public.student_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES student_profiles(id) ON DELETE CASCADE,

    -- Learning preferences
    preferred_study_hours JSONB DEFAULT '{"morning": 2, "afternoon": 2, "evening": 3, "night": 1}'::jsonb,
    difficulty_preference DECIMAL(3,2) DEFAULT 0.6 CHECK (difficulty_preference BETWEEN 0.1 AND 1.0),
    subject_priorities JSONB DEFAULT '{"mathematics": 0.4, "physics": 0.35, "chemistry": 0.25}'::jsonb,

    -- UI/UX preferences
    language_preference VARCHAR(10) DEFAULT 'en',
    theme_preference VARCHAR(20) DEFAULT 'light',
    notification_settings JSONB DEFAULT '{"email": true, "push": true, "sms": false}'::jsonb,

    -- Accessibility settings
    accessibility_settings JSONB DEFAULT '{"high_contrast": false, "large_text": false, "screen_reader": false}'::jsonb,

    -- AI personalization settings
    ai_explanation_level VARCHAR(20) DEFAULT 'detailed' CHECK (ai_explanation_level IN ('brief', 'detailed', 'comprehensive')),
    mistake_analysis_enabled BOOLEAN DEFAULT TRUE,
    performance_tracking_enabled BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

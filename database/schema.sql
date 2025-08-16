-- Supabase Database Schema for Customer Feedback Dashboard

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Custom types
CREATE TYPE user_role AS ENUM ('demo_viewer', 'member', 'admin');
CREATE TYPE feedback_source AS ENUM ('manual', 'twitter', 'google_maps', 'csv_import', 'api');
CREATE TYPE sentiment_label AS ENUM ('positive', 'negative', 'neutral');
CREATE TYPE urgency_level AS ENUM ('low', 'medium', 'high');
CREATE TYPE job_status AS ENUM ('queued', 'processing', 'completed', 'failed', 'cancelled');

-- Users table (extends Supabase auth.users)
CREATE TABLE profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    role user_role DEFAULT 'member',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Projects table
CREATE TABLE projects (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    owner_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    is_demo BOOLEAN DEFAULT FALSE,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Feedbacks table
CREATE TABLE feedbacks (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE NOT NULL,
    content TEXT NOT NULL,
    source feedback_source DEFAULT 'manual',
    source_url TEXT,
    source_metadata JSONB DEFAULT '{}',
    author_name TEXT,
    author_handle TEXT,
    posted_at TIMESTAMP WITH TIME ZONE,
    language TEXT DEFAULT 'auto',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Analyses table (results from AI pipeline)
CREATE TABLE analyses (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    feedback_id UUID REFERENCES feedbacks(id) ON DELETE CASCADE NOT NULL,
    
    -- Language detection
    detected_language TEXT,
    
    -- Sentiment analysis
    sentiment_label sentiment_label,
    sentiment_score FLOAT,
    sentiment_confidence FLOAT,
    sentiment_model TEXT,
    
    -- Topic classification
    topics JSONB DEFAULT '[]', -- [{label, score, confidence}]
    topics_fixed JSONB DEFAULT '[]', -- Refined by Granite
    
    -- Entity extraction (IBM Watson NLU)
    entities JSONB DEFAULT '[]',
    keywords JSONB DEFAULT '[]',
    categories JSONB DEFAULT '[]',
    
    -- Granite insights
    granite_summary TEXT,
    granite_insights JSONB DEFAULT '{}', -- {urgency, action_recommendation, etc}
    granite_tie_break JSONB DEFAULT '{}', -- If sentiment confidence was low
    granite_raw TEXT, -- Raw response for debugging
    
    -- Processing metadata
    processing_time_ms INTEGER,
    errors JSONB DEFAULT '[]',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(feedback_id) -- One analysis per feedback
);

-- Orchestrate jobs table
CREATE TABLE orchestrate_jobs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    feedback_id UUID REFERENCES feedbacks(id) ON DELETE CASCADE NOT NULL,
    analysis_id UUID REFERENCES analyses(id) ON DELETE CASCADE NOT NULL,
    
    kind TEXT NOT NULL, -- 'ticket', 'alert', 'email', etc
    status job_status DEFAULT 'queued',
    
    payload JSONB NOT NULL, -- Job data to send to Orchestrate
    response JSONB DEFAULT '{}', -- Response from Orchestrate
    external_ref TEXT, -- Reference ID from external system
    
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit logs table
CREATE TABLE audit_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id UUID,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_projects_owner_id ON projects(owner_id);
CREATE INDEX idx_projects_is_demo ON projects(is_demo);

CREATE INDEX idx_feedbacks_project_id ON feedbacks(project_id);
CREATE INDEX idx_feedbacks_source ON feedbacks(source);
CREATE INDEX idx_feedbacks_created_at ON feedbacks(created_at);
CREATE INDEX idx_feedbacks_content_trgm ON feedbacks USING gin(content gin_trgm_ops);

CREATE INDEX idx_analyses_feedback_id ON analyses(feedback_id);
CREATE INDEX idx_analyses_sentiment_label ON analyses(sentiment_label);
CREATE INDEX idx_analyses_created_at ON analyses(created_at);

CREATE INDEX idx_orchestrate_jobs_status ON orchestrate_jobs(status);
CREATE INDEX idx_orchestrate_jobs_scheduled_at ON orchestrate_jobs(scheduled_at);
CREATE INDEX idx_orchestrate_jobs_feedback_id ON orchestrate_jobs(feedback_id);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- Row Level Security (RLS) Policies

-- Enable RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedbacks ENABLE ROW LEVEL SECURITY;
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE orchestrate_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can read own profile" ON profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON profiles
    FOR UPDATE USING (auth.uid() = id);

-- Projects policies
CREATE POLICY "Users can read own projects and demo projects" ON projects
    FOR SELECT USING (
        owner_id = auth.uid() OR 
        is_demo = true OR
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

CREATE POLICY "Users can create own projects" ON projects
    FOR INSERT WITH CHECK (owner_id = auth.uid());

CREATE POLICY "Users can update own projects" ON projects
    FOR UPDATE USING (
        owner_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

CREATE POLICY "Users can delete own projects" ON projects
    FOR DELETE USING (
        owner_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Feedbacks policies
CREATE POLICY "Users can read feedbacks from accessible projects" ON feedbacks
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM projects p 
            WHERE p.id = project_id AND (
                p.owner_id = auth.uid() OR 
                p.is_demo = true OR
                EXISTS (
                    SELECT 1 FROM profiles 
                    WHERE id = auth.uid() AND role = 'admin'
                )
            )
        )
    );

CREATE POLICY "Users can insert feedbacks to own projects" ON feedbacks
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM projects p 
            WHERE p.id = project_id AND p.owner_id = auth.uid()
        ) OR
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

CREATE POLICY "Users can update feedbacks in own projects" ON feedbacks
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM projects p 
            WHERE p.id = project_id AND p.owner_id = auth.uid()
        ) OR
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

CREATE POLICY "Users can delete feedbacks from own projects" ON feedbacks
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM projects p 
            WHERE p.id = project_id AND p.owner_id = auth.uid()
        ) OR
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Analyses policies (similar to feedbacks)
CREATE POLICY "Users can read analyses from accessible projects" ON analyses
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM feedbacks f
            JOIN projects p ON f.project_id = p.id
            WHERE f.id = feedback_id AND (
                p.owner_id = auth.uid() OR 
                p.is_demo = true OR
                EXISTS (
                    SELECT 1 FROM profiles 
                    WHERE id = auth.uid() AND role = 'admin'
                )
            )
        )
    );

CREATE POLICY "Service role can manage analyses" ON analyses
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

-- Orchestrate jobs policies
CREATE POLICY "Users can read orchestrate jobs from accessible projects" ON orchestrate_jobs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM feedbacks f
            JOIN projects p ON f.project_id = p.id
            WHERE f.id = feedback_id AND (
                p.owner_id = auth.uid() OR
                EXISTS (
                    SELECT 1 FROM profiles 
                    WHERE id = auth.uid() AND role = 'admin'
                )
            )
        )
    );

CREATE POLICY "Service role can manage orchestrate jobs" ON orchestrate_jobs
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

-- Audit logs policies
CREATE POLICY "Users can read own audit logs" ON audit_logs
    FOR SELECT USING (
        user_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

CREATE POLICY "Service role can insert audit logs" ON audit_logs
    FOR INSERT WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

-- Functions for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_feedbacks_updated_at BEFORE UPDATE ON feedbacks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_analyses_updated_at BEFORE UPDATE ON analyses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orchestrate_jobs_updated_at BEFORE UPDATE ON orchestrate_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Demo data
-- Note: In Supabase, users must be created through auth.users first
-- This can be done via the Supabase dashboard or auth API

-- Create demo users in auth.users (run this in Supabase SQL editor after creating the users via dashboard)
-- For now, we'll insert profiles manually after creating users via Supabase Auth

-- Example profiles (insert after creating users via Supabase Auth):
-- INSERT INTO profiles (id, email, full_name, role) VALUES
--     ('user-uuid-from-auth-users', 'demo@cfd.app', 'Demo User', 'demo_viewer'),
--     ('user-uuid-from-auth-users', 'member@cfd.app', 'Member User', 'member'),
--     ('user-uuid-from-auth-users', 'admin@cfd.app', 'Admin User', 'admin');

-- Demo project and data will be created after setting up users
-- Run this AFTER creating users via Supabase Auth dashboard:

-- Step 1: Create demo users via Supabase Auth dashboard or API
-- Step 2: Insert their profiles 
-- Step 3: Run the following SQL to create demo project and data:

/*
-- Replace 'demo-user-uuid' with actual UUID from auth.users table
INSERT INTO projects (id, name, description, owner_id, is_demo) VALUES
    ('00000000-0000-0000-0000-000000000001', 'DEMO - CoffeeShop', 'Demo project showing customer feedback analysis for a coffee shop', 'demo-user-uuid', true);

-- Demo feedbacks
INSERT INTO feedbacks (id, project_id, content, source, author_name, posted_at, language) VALUES
    ('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'Kopi di sini enak banget! Pelayanannya juga cepat. Recommended!', 'google_maps', 'Sarah M.', NOW() - INTERVAL '2 days', 'id'),
    ('00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', 'Disappointing experience. Coffee was cold and service was slow. Will not return.', 'twitter', 'John D.', NOW() - INTERVAL '1 day', 'en'),
    ('00000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000001', 'Tempatnya cozy, tapi harganya agak mahal untuk ukuran porsi segitu. Wifi juga lambat.', 'manual', 'Rina S.', NOW() - INTERVAL '3 hours', 'id'),
    ('00000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000001', 'Great atmosphere and excellent barista skills. The latte art was amazing!', 'google_maps', 'Mike T.', NOW() - INTERVAL '1 hour', 'en'),
    ('00000000-0000-0000-0000-000000000005', '00000000-0000-0000-0000-000000000001', 'Makanan di sini juga enak lho, bukan cuma kopinya. Croissant-nya crispy!', 'manual', 'Lisa W.', NOW() - INTERVAL '30 minutes', 'id');

-- Demo analyses
INSERT INTO analyses (feedback_id, detected_language, sentiment_label, sentiment_score, sentiment_confidence, topics, granite_summary, granite_insights) VALUES
    ('00000000-0000-0000-0000-000000000001', 'id', 'positive', 0.89, 0.92, '[{"label": "layanan", "score": 0.85}, {"label": "produk", "score": 0.78}]', 'Customer sangat puas dengan kualitas kopi dan kecepatan pelayanan.', '{"urgency": "low", "action_recommendation": "Pertahankan standar pelayanan yang baik"}'),
    ('00000000-0000-0000-0000-000000000002', 'en', 'negative', 0.82, 0.88, '[{"label": "layanan", "score": 0.92}, {"label": "produk", "score": 0.76}]', 'Customer unhappy with cold coffee and slow service.', '{"urgency": "high", "action_recommendation": "Address service quality issues immediately"}'),
    ('00000000-0000-0000-0000-000000000003', 'id', 'neutral', 0.65, 0.71, '[{"label": "harga", "score": 0.88}, {"label": "lokasi", "score": 0.67}]', 'Mixed feedback - likes ambiance but concerned about pricing and wifi.', '{"urgency": "medium", "action_recommendation": "Review pricing strategy and improve wifi infrastructure"}'),
    ('00000000-0000-0000-0000-000000000004', 'en', 'positive', 0.91, 0.94, '[{"label": "layanan", "score": 0.89}, {"label": "lokasi", "score": 0.72}]', 'Excellent feedback highlighting barista skills and atmosphere.', '{"urgency": "low", "action_recommendation": "Use as positive testimonial for marketing"}'),
    ('00000000-0000-0000-0000-000000000005', 'id', 'positive', 0.84, 0.87, '[{"label": "produk", "score": 0.91}]', 'Positive feedback about food quality beyond just coffee.', '{"urgency": "low", "action_recommendation": "Promote food menu alongside coffee offerings"}');
*/

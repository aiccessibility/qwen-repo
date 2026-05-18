-- Initialize Accessibility Database

-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    organization VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user', -- user, admin, enterprise
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create audits table
CREATE TABLE IF NOT EXISTS audits (
    id VARCHAR(255) PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    url VARCHAR(2048) NOT NULL,
    wcag_level VARCHAR(10) DEFAULT 'AA',
    wcag_version VARCHAR(10) DEFAULT '2.2',
    status VARCHAR(50) DEFAULT 'pending', -- pending, scanning, analyzing, completed, failed
    progress INTEGER DEFAULT 0,
    depth INTEGER DEFAULT 1,
    include_screenshots BOOLEAN DEFAULT true,
    html_content TEXT,
    screenshots JSONB DEFAULT '[]',
    wcag_violations JSONB DEFAULT '[]',
    severity_summary JSONB DEFAULT '{}',
    recommendations JSONB DEFAULT '[]',
    report_url VARCHAR(2048),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Create monitors table for continuous monitoring
CREATE TABLE IF NOT EXISTS monitors (
    id VARCHAR(255) PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    url VARCHAR(2048) NOT NULL,
    schedule_cron VARCHAR(100) DEFAULT '0 0 * * *', -- Daily at midnight
    wcag_level VARCHAR(10) DEFAULT 'AA',
    wcag_version VARCHAR(10) DEFAULT '2.2',
    status VARCHAR(50) DEFAULT 'active', -- active, paused, stopped
    last_audit_at TIMESTAMP WITH TIME ZONE,
    next_audit_at TIMESTAMP WITH TIME ZONE,
    alert_email VARCHAR(255),
    alert_webhook VARCHAR(2048),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create audit_history for tracking changes over time
CREATE TABLE IF NOT EXISTS audit_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_id VARCHAR(255) REFERENCES audits(id) ON DELETE CASCADE,
    monitor_id VARCHAR(255) REFERENCES monitors(id) ON DELETE CASCADE,
    snapshot_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    violations_count INTEGER DEFAULT 0,
    critical_count INTEGER DEFAULT 0,
    serious_count INTEGER DEFAULT 0,
    moderate_count INTEGER DEFAULT 0,
    minor_count INTEGER DEFAULT 0,
    score DECIMAL(5,2), -- Accessibility score 0-100
    changes_detected JSONB DEFAULT '[]'
);

-- Create WCAG rules reference table
CREATE TABLE IF NOT EXISTS wcag_rules (
    id VARCHAR(50) PRIMARY KEY, -- e.g., "1.1.1"
    version VARCHAR(10) NOT NULL, -- "2.1", "2.2"
    level VARCHAR(10) NOT NULL, -- "A", "AA", "AAA"
    principle VARCHAR(100) NOT NULL, -- "Perceivable", "Operable", etc.
    guideline VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    how_to_meet TEXT,
    embedding vector(768) -- For semantic search with pgvector
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_audits_user_id ON audits(user_id);
CREATE INDEX IF NOT EXISTS idx_audits_status ON audits(status);
CREATE INDEX IF NOT EXISTS idx_audits_created_at ON audits(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_monitors_user_id ON monitors(user_id);
CREATE INDEX IF NOT EXISTS idx_monitors_status ON monitors(status);
CREATE INDEX IF NOT EXISTS idx_monitors_next_audit ON monitors(next_audit_at) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_audit_history_audit_id ON audit_history(audit_id);
CREATE INDEX IF NOT EXISTS idx_audit_history_snapshot_date ON audit_history(snapshot_date DESC);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS idx_wcag_rules_embedding ON wcag_rules USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_audits_updated_at BEFORE UPDATE ON audits
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_monitors_updated_at BEFORE UPDATE ON monitors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample WCAG rules (subset for demo)
INSERT INTO wcag_rules (id, version, level, principle, guideline, title, description) VALUES
('1.1.1', '2.1', 'A', 'Perceivable', 'Text Alternatives', 'Non-text Content', 
 'All non-text content that is presented to the user has a text alternative that serves the equivalent purpose.'),
('1.2.1', '2.1', 'A', 'Perceivable', 'Time-based Media', 'Audio-only and Video-only (Prerecorded)',
 'For prerecorded audio-only and prerecorded video-only media, alternatives are provided.'),
('1.3.1', '2.1', 'A', 'Perceivable', 'Adaptable', 'Info and Relationships',
 'Information, structure, and relationships conveyed through presentation can be programmatically determined.'),
('1.4.1', '2.1', 'A', 'Perceivable', 'Distinguishable', 'Use of Color',
 'Color is not used as the only visual means of conveying information.'),
('1.4.3', '2.1', 'AA', 'Perceivable', 'Distinguishable', 'Contrast (Minimum)',
 'The visual presentation of text and images of text has a contrast ratio of at least 4.5:1.'),
('2.1.1', '2.1', 'A', 'Operable', 'Keyboard Accessible', 'Keyboard',
 'All functionality of the content is operable through a keyboard interface.'),
('2.4.1', '2.1', 'A', 'Operable', 'Navigable', 'Bypass Blocks',
 'A mechanism is available to bypass blocks of content that are repeated on multiple Web pages.'),
('2.4.6', '2.1', 'AA', 'Operable', 'Navigable', 'Headings and Labels',
 'Headings and labels describe topic or purpose.'),
('3.1.1', '2.1', 'A', 'Understandable', 'Readable', 'Language of Page',
 'The default human language of each Web page can be programmatically determined.'),
('4.1.1', '2.1', 'A', 'Robust', 'Compatible', 'Parsing',
 'In content implemented using markup languages, elements have complete start and end tags.'),
('4.1.2', '2.1', 'A', 'Robust', 'Compatible', 'Name, Role, Value',
 'For all user interface components, the name and role can be programmatically determined.');

COMMENT ON TABLE audits IS 'Stores accessibility audit results for web pages';
COMMENT ON TABLE monitors IS 'Continuous monitoring configurations for URLs';
COMMENT ON TABLE audit_history IS 'Historical snapshots of audit results for trend analysis';
COMMENT ON TABLE wcag_rules IS 'Reference table for WCAG success criteria';

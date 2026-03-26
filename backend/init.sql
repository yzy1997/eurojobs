-- EuroJobs Database Schema

-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(100),
    country VARCHAR(50) NOT NULL,
    category VARCHAR(50),
    salary_range VARCHAR(100),
    description TEXT,
    url TEXT NOT NULL,
    source VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    likes INTEGER DEFAULT 0
);

-- Comments table
CREATE TABLE IF NOT EXISTS comments (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    author VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ad slots table
CREATE TABLE IF NOT EXISTS ad_slots (
    id SERIAL PRIMARY KEY,
    position VARCHAR(50) NOT NULL,
    ad_code TEXT,
    active BOOLEAN DEFAULT true
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_jobs_country ON jobs(country);
CREATE INDEX IF NOT EXISTS idx_jobs_category ON jobs(category);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_comments_job_id ON comments(job_id);

-- Insert some sample data
INSERT INTO jobs (title, company, location, country, category, salary_range, description, url, source, likes) VALUES
('Senior Python Developer', 'TechCorp GmbH', 'Berlin', '德国', '技术', '€70,000 - €100,000', 'We are looking for an experienced Python developer to join our team. Remote work available.', 'https://example.com/job1', 'Indeed', 42),
('Frontend Engineer', 'WebSolutions Paris', 'Paris', '法国', '技术', '€55,000 - €75,000', 'Join our frontend team to build amazing web applications.', 'https://example.com/job2', 'LinkedIn', 28),
('Data Analyst', 'FinData London', 'London', '英国', '金融', '£45,000 - £60,000', 'Analyze financial data and create reports for clients.', 'https://example.com/job3', 'Indeed', 35),
('Marketing Manager', 'BrandCo Amsterdam', 'Amsterdam', '荷兰', '市场', '€50,000 - €70,000', 'Lead our marketing team and drive brand awareness.', 'https://example.com/job4', 'LinkedIn', 19),
('UX Designer', 'DesignHub Stockholm', 'Stockholm', '瑞典', '设计', 'SEK 50,000 - 70,000', 'Create beautiful and intuitive user interfaces.', 'https://example.com/job5', 'Indeed', 31);

-- Sample comments
INSERT INTO comments (job_id, content, author, created_at) VALUES
(1, '很棒的职位！请问需要签证支持吗？', '张三', '2024-01-15 10:30:00'),
(1, '请问这个岗位接受远程吗？', '李四', '2024-01-15 11:00:00'),
(2, '公司氛围怎么样？', '王五', '2024-01-14 09:20:00');

-- Default ad slots
INSERT INTO ad_slots (position, ad_code, active) VALUES
('header', '', true),
('sidebar', '', true),
('between_jobs', '', true);
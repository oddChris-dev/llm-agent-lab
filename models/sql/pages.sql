DROP TABLE IF EXISTS pages;
CREATE TABLE pages (
    url_hash CHAR(64) NOT NULL,               -- Hash of the URL (e.g., SHA-256)
    session_id INT NOT NULL,                  -- The session this page is associated with
    url VARCHAR(2048) NOT NULL,               -- The actual page URL
    title VARCHAR(500) DEFAULT NULL,          -- The page title, NULL if not yet loaded
    body TEXT DEFAULT NULL,                   -- The page body, NULL if not yet loaded
    summary TEXT DEFAULT NULL,                -- AI-generated summary, NULL if not yet summarized
    parent_url_hash CHAR(64) DEFAULT NULL,    -- Refers to the hash of the parent URL (self-referencing foreign key)
    search_term VARCHAR(500) DEFAULT NULL,    -- The search query that resulted in this page
    search_rank INT DEFAULT NULL,             -- The rank of this page in the search results
    last_loaded TIMESTAMP DEFAULT NULL,       -- Last time the page was loaded
    last_opened TIMESTAMP DEFAULT NULL,       -- Last time the page was opened (shown to the user)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- When the page was first seen
    is_body_null BOOLEAN GENERATED ALWAYS AS (body IS NULL),  -- Tracks if body is NULL
    is_summary_null BOOLEAN GENERATED ALWAYS AS (summary IS NULL),  -- Tracks if summary is NULL
    PRIMARY KEY (url_hash, session_id)       -- Composite primary key for session and page
);

-- New index for fast lookups and deletions by session_id
CREATE INDEX idx_pages_session_id ON pages(session_id);

-- Index for efficiently finding pages where the body is NULL
CREATE INDEX idx_pages_body_null ON pages(is_body_null);

-- Index for efficiently finding pages where the summary is NULL
CREATE INDEX idx_pages_summary_null ON pages(is_summary_null);

-- Index for efficiently finding pages by search term and offset
CREATE INDEX idx_pages_search ON pages(search_term);

-- Index for quickly finding pages based on their parent URL hash
CREATE INDEX idx_pages_parent_url_hash ON pages(parent_url_hash);

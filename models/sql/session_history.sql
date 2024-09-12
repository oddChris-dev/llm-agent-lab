DROP TABLE IF EXISTS session_history;

-- Table to store the history of actions or events in the session
CREATE TABLE session_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT,
    role VARCHAR(255),
    content TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- Add an index on the timestamp column for efficient sorting and range queries
CREATE INDEX idx_timestamp ON session_history (timestamp);

-- Add an index on the role column for efficient filtering
CREATE INDEX idx_role ON session_history (role);

-- Add a composite index on session_id, role, and timestamp for optimized filtering and ordering
CREATE INDEX idx_session_role_timestamp ON session_history (session_id, role, timestamp);

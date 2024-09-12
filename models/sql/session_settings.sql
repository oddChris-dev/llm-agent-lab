DROP TABLE IF EXISTS session_settings;

-- Table to store settings related to a session
CREATE TABLE session_settings (
    session_id INT,
    name VARCHAR(255),
    value TEXT,
    PRIMARY KEY (session_id, name),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

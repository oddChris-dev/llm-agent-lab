-- Table to store agent information
DROP TABLE IF EXISTS agents;

CREATE TABLE agents (
    name VARCHAR(255) PRIMARY KEY NOT NULL,
    role VARCHAR(255),
    voice VARCHAR(255),
    prompt TEXT
);

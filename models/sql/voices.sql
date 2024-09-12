-- Table to store voice files with name as the primary key
DROP TABLE IF EXISTS voices;

CREATE TABLE voices (
    name VARCHAR(255) PRIMARY KEY,
    data LONGBLOB NOT NULL
);
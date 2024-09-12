-- Table to store game information
DROP TABLE IF EXISTS game_variables;
DROP TABLE IF EXISTS games;

CREATE TABLE games (
    name VARCHAR(255) PRIMARY KEY NOT NULL,
    rules TEXT NOT NULL
);

-- Table to store game variables
CREATE TABLE game_variables (
    game_name VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    value TEXT,
    PRIMARY KEY (game_name, name),
    FOREIGN KEY (game_name) REFERENCES games(name) ON DELETE CASCADE
);

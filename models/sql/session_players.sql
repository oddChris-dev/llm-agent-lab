DROP TABLE IF EXISTS session_players;

-- Table to store the players involved in a session
CREATE TABLE session_players (
    session_id INT,
    turn_order INT, -- To define the turn order of players
    player VARCHAR(255) NOT NULL,
    voice VARCHAR(255), -- Voice property; if NULL, the player will not speak
    PRIMARY KEY (session_id, turn_order), -- Primary key is session_id and turn_order
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

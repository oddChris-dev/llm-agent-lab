DROP TABLE IF EXISTS sessions;

-- Table to store the basic session information, including the game and judge
CREATE TABLE sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    game VARCHAR(255) NOT NULL,
    judge VARCHAR(255) NOT NULL,
    summary VARCHAR(255) NOT NULL
);


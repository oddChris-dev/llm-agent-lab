class SessionPlayerModel:
    def __init__(self, db, session_id, turn_order, player, voice=None):
        self.db = db
        self.session_id = session_id
        self.turn_order = turn_order
        self.player = player
        self.voice = voice  # None means the player won't speak

    def save(self):
        query = """
        INSERT INTO session_players (session_id, turn_order, player, voice)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        player = VALUES(player),
        voice = VALUES(voice);
        """
        self.db.execute_query(
            query,
            (self.session_id, self.turn_order, self.player, self.voice)
        )

    @classmethod
    def get_by_session_id(cls, db, session_id):
        """Retrieve all players for a specific session_id."""
        query = "SELECT turn_order, player, voice FROM session_players WHERE session_id = %s ORDER BY turn_order;"
        results = db.fetch_results(query, (session_id,))
        return [cls(db, session_id, row[0], row[1], row[2]) for row in results]

    @classmethod
    def get(cls, db, session_id, turn_order):
        """Retrieve a specific player by session_id and turn_order."""
        query = "SELECT session_id, turn_order, player, voice FROM session_players WHERE session_id = %s AND turn_order = %s;"
        result = db.fetch_results(query, (session_id, turn_order))
        if result:
            row = result[0]
            return cls(db, row[0], row[1], row[2], row[3])
        else:
            return None

    @classmethod
    def delete_by_session_id(cls, db, session_id):
        """Delete all players for a given session_id."""
        query = "DELETE FROM session_players WHERE session_id = %s;"
        db.execute_query(query, (session_id,))

    def delete(self):
        """Delete a specific player by session_id and turn_order."""
        query = "DELETE FROM session_players WHERE session_id = %s and turn_order = %s;"
        self.db.execute_query(query, (self.session_id, self.turn_order))

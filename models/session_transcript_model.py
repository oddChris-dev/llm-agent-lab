class SessionTranscriptModel:
    def __init__(self, db, id, session_id, agent, url, content, timestamp=None):
        self.db = db
        self.id = id
        self.session_id = session_id
        self.agent = agent
        self.url = url
        self.content = content
        self.timestamp = timestamp

    @classmethod
    def get_all(cls, db):
        query = "SELECT id, session_id, agent, url, content, timestamp FROM transcripts order by timestamp DESC;"
        results = db.fetch_results(query)
        transcripts = []
        for row in results:
            transcripts.append(cls(db, row[0], row[1], row[2], row[3], row[4], row[5]))
        return transcripts

    @classmethod
    def get(cls, db, id):
        query = "SELECT id, session_id, agent, url, content, timestamp FROM transcripts WHERE id = %s;"
        result = db.fetch_results(query, (id,))
        if result:
            row = result[0]
            return cls(db, row[0], row[1], row[2], row[3], row[4], row[5])
        return None

    @classmethod
    def get_new_transcripts_since(cls, db, timestamp):
        """Retrieve all transcripts created after a specific timestamp."""
        query = """
        SELECT id, session_id, agent, url, content, timestamp
        FROM transcripts
        WHERE timestamp > %s
        ORDER BY timestamp;
        """
        results = db.fetch_results(query, (timestamp,))
        transcripts = []
        for row in results:
            transcripts.append(cls(db, row[0], row[1], row[2], row[3], row[4], row[5]))
        return transcripts

    @classmethod
    def get_new_session_transcripts_since(cls, db, session, timestamp):
        """Retrieve all transcripts created after a specific timestamp."""
        query = """
        SELECT id, session_id, agent, url, content, timestamp
        FROM transcripts
        WHERE session_id = %s and timestamp > %s
        ORDER BY timestamp;
        """
        results = db.fetch_results(query, (session, timestamp,))
        transcripts = []
        for row in results:
            transcripts.append(cls(db, row[0], row[1], row[2], row[3], row[4], row[5]))
        return transcripts

    @classmethod
    def get_by_session_id(cls, db, session_id):
        query = ("SELECT id, session_id, agent, url, content, timestamp "
                 "FROM transcripts WHERE session_id = %s order by timestamp DESC;")
        results = db.fetch_results(query, (session_id,))
        transcripts = []
        for row in results:
            transcripts.append(cls(db, row[0], row[1], row[2], row[3], row[4], row[5]))
        return transcripts

    @classmethod
    def delete_by_session_id(cls, db, session_id):
        query = "DELETE FROM transcripts WHERE session_id = %s;"
        db.execute_query(query, (session_id,))

    def save(self):
        if self.id:
            # Update an existing transcript
            query = """
            UPDATE transcripts
            SET session_id = %s, agent = %s, url = %s, content = %s
            WHERE id = %s;
            """
            self.db.execute_query(
                query,
                (self.session_id, self.agent, self.url, self.content, self.id)
            )
        else:
            # Insert a new transcript and retrieve the auto-incremented id
            query = """
            INSERT INTO transcripts (session_id, agent, url, content)
            VALUES (%s, %s, %s, %s);
            """
            self.id = self.db.execute_query(
                query,
                (self.session_id, self.agent, self.url, self.content),
                return_last_insert_id=True
            )

    def delete(self):
        if self.id:
            query = "DELETE FROM transcripts WHERE id = %s;"
            self.db.execute_query(query, (self.id,))

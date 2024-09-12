class AgentModel:
    def __init__(self, db, name, prompt, voice, role):
        self.db = db
        self.name = name
        self.prompt = prompt
        self.voice = voice
        self.role = role

    @classmethod
    def get_all(cls, db):
        query = "SELECT name, prompt, voice, role FROM agents;"
        results = db.fetch_results(query)
        return [cls(db, row[0], row[1], row[2], row[3]) for row in results]

    @classmethod
    def get(cls, db, name):
        query = "SELECT name, prompt, voice, role FROM agents WHERE name = %s;"
        result = db.fetch_results(query, (name,))
        if result:
            row = result[0]
            return cls(db, row[0], row[1], row[2], row[3])
        return None

    def save(self):
        query = """
        INSERT INTO agents (name, prompt, voice, role)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        prompt = VALUES(prompt),
        voice = VALUES(voice),
        role = VALUES(role);
        """
        self.db.execute_query(query, (self.name, self.prompt, self.voice, self.role))

    def delete(self):
        query = "DELETE FROM agents WHERE name = %s;"
        self.db.execute_query(query, (self.name,))

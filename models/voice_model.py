class VoiceModel:
    def __init__(self, db, name):
        self.db = db
        self.name = name
        self.data = None  # Binary data for the WAV file, use get_data() to load

    @classmethod
    def get_all(cls, db):
        query = "SELECT name FROM voices;"
        results = db.fetch_results(query)
        return [cls(db, row[0]) for row in results]

    def get_data(self):
        if not self.data:
            query = "SELECT data FROM voices WHERE name = %s;"
            result = self.db.fetch_results(query, (self.name,), binary=True)
            if result:
                row = result[0]
                self.data = row[0]

        return self.data

    def save(self):
        query = """
        INSERT INTO voices (name, data)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE
        data = VALUES(data);
        """
        self.db.execute_query(query, (self.name, self.data))

    def delete(self):
        query = "DELETE FROM voices WHERE name = %s;"
        self.db.execute_query(query, (self.name,))


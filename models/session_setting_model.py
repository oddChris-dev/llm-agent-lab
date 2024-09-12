from systems.database import Database


class SessionSettingModel:
    def __init__(self, db, session_id, name, value):
        self.db = db
        self.session_id = session_id
        self.name = name
        self.value = value

    def save(self):
        query = """
        INSERT INTO session_settings (session_id, name, value)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
        value = VALUES(value);
        """
        self.db.execute_query(
            query,
            (self.session_id, self.name, self.value)
        )

    @classmethod
    def get_by_session_id(cls, db, session_id):
        """Retrieve all settings for a specific session_id as instances of SettingsModel."""
        query = "SELECT name, value FROM session_settings WHERE session_id = %s;"
        results = db.fetch_results(query, (session_id,))
        # Return a list of SettingsModel instances
        return [cls(db, session_id, row[0], row[1]) for row in results]

    @classmethod
    def get(cls, db, session_id, name):
        """Retrieve a specific setting by session_id and name."""
        query = "SELECT session_id, name, value FROM session_settings WHERE session_id = %s AND name = %s;"
        result = Database().fetch_results(query, (session_id, name))
        if result:
            row = result[0]
            return cls(db, row[0], row[1], row[2])
        else:
            return cls(db, session_id, name, '')

    @classmethod
    def delete_by_session_id(cls, db, session_id):
        query = "DELETE FROM session_settings WHERE session_id = %s;"
        db.execute_query(query, (session_id,))

    def delete(self):
        query = "DELETE FROM session_settings WHERE session_id = %s and name = %s;"
        self.db.execute_query(query, (self.session_id, self.name))


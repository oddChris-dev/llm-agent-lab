class SessionHistoryModel:
    def __init__(self, db, id, session_id, role, content, timestamp=None):
        self.db = db
        self.id = id
        self.session_id = session_id
        self.role = role
        self.content = content
        self.timestamp = timestamp

    @classmethod
    def get_by_session_id(cls, db, session_id):
        query = ("SELECT id, session_id, role, content, timestamp "
                 "FROM session_history WHERE session_id = %s ORDER BY timestamp DESC;")
        results = db.fetch_results(query, (session_id,))
        return [cls(db, row[0], row[1], row[2], row[3], row[4]) for row in results]

    @classmethod
    def get(cls, db, id):
        query = ("SELECT id, session_id, role, content, timestamp "
                 "FROM session_history WHERE id = %s;")
        results = db.fetch_results(query, (id,))
        row = results[0]
        return cls(db, row[0], row[1], row[2], row[3], row[4])


    @classmethod
    def get_latest_by_role(cls, db, session_id, role, n, use_wildcard=False):
        if use_wildcard:
            query = """
            SELECT id, role, content, timestamp 
            FROM session_history 
            WHERE session_id = %s AND role LIKE %s 
            ORDER BY timestamp DESC 
            LIMIT %s;
            """
            role_param = role.replace('*', '%')  # role should already include any wildcard characters (e.g., 'agent-%')
        else:
            query = """
            SELECT id, role, content, timestamp 
            FROM session_history 
            WHERE session_id = %s AND role = %s 
            ORDER BY timestamp DESC 
            LIMIT %s;
            """
            role_param = role

        results = db.fetch_results(query, (session_id, role_param, n))
        return [cls(db, session_id, row[0], row[1], row[2], row[3]) for row in results]

    @classmethod
    def delete_by_session_id(cls, db, session_id):
        query = "DELETE FROM session_history WHERE session_id = %s;"
        db.execute_query(query, (session_id,))

    def save(self):
        if not self.id:
            # Use the provided timestamp
            insert_query = """
            INSERT INTO session_history (session_id, role, content)
            VALUES (%s, %s, %s);
            """
            self.id = self.db.execute_query(insert_query, (self.session_id, self.role, self.content))
        else:
            # Omit timestamp to use the default CURRENT_TIMESTAMP
            insert_query = """
            INSERT INTO session_history (id, session_id, role, content)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            role = VALUES(role), content = VALUES(content), session_id = VALUES(session_id);
            """
            self.db.execute_query(insert_query, (self.id, self.session_id, self.role, self.content))

    def delete(self):
        if self.id:
            query = "DELETE FROM session_history WHERE id = %s;"
            self.db.execute_query(query, (self.id,))

    @classmethod
    def get_paginated_by_session_id(cls, db, session_id, page, per_page):
        """Retrieve paginated session history entries."""
        offset = (page - 1) * per_page
        query = ("SELECT id, session_id, role, content, timestamp "
                 "FROM session_history "
                 "WHERE session_id = %s "
                 "ORDER BY timestamp DESC "
                 "LIMIT %s OFFSET %s;")
        results = db.fetch_results(query, (session_id, per_page, offset))
        return [cls(db, row[0], row[1], row[2], row[3], row[4]) for row in results]

    @classmethod
    def get_total_count_by_session_id(cls, db, session_id):
        """Retrieve the total count of history entries for a session."""
        query = "SELECT COUNT(*) FROM session_history WHERE session_id = %s;"
        result = db.fetch_results(query, (session_id,))
        return result[0][0]  # Return the count
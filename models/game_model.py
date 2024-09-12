

class GameModel:
    def __init__(self, db, name, rules, variables):
        self.db = db
        self.name = name
        self.rules = rules
        self.variables = variables  # Assuming variables is a dictionary

    @classmethod
    def get_all(cls, db):
        query = "SELECT name, rules FROM games;"
        results = db.fetch_results(query)
        games = []
        for row in results:
            variables = cls.get_variables(db, row[0])
            games.append(cls(db, row[0], row[1], variables))
        return games

    @classmethod
    def get(cls, db, name):
        query = "SELECT name, rules FROM games WHERE name = %s;"
        result = db.fetch_results(query, (name,))
        if result:
            row = result[0]
            variables = cls.get_variables(db, row[0])
            return cls(db, row[0], row[1], variables)
        return None

    @classmethod
    def get_variables(cls, db, game_name):
        query = "SELECT name, value FROM game_variables WHERE game_name = %s;"
        results = db.fetch_results(query, (game_name,))
        return {row[0]: row[1] for row in results}

    def save(self):
        query = """
        INSERT INTO games (name, rules)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE
        rules = VALUES(rules);
        """
        self.db.execute_query(query, (self.name, self.rules))
        self.save_variables()

    def save_variables(self):
        delete_query = "DELETE FROM game_variables WHERE game_name = %s;"
        self.db.execute_query(delete_query, (self.name,))

        insert_query = """
        INSERT INTO game_variables (game_name, name, value)
        VALUES (%s, %s, %s);
        """
        for name, value in self.variables.items():
            self.db.execute_query(insert_query, (self.name, name, value))

    def delete(self):
        self.delete_variables()
        query = "DELETE FROM games WHERE name = %s;"
        self.db.execute_query(query, (self.name,))

    def delete_variables(self):
        query = "DELETE FROM game_variables WHERE game_name = %s;"
        self.db.execute_query(query, (self.name,))

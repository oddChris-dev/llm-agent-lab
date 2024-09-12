from models.page_model import PageModel
from models.session_history_model import SessionHistoryModel
from models.session_setting_model import SessionSettingModel
from models.session_player_model import SessionPlayerModel
from models.session_transcript_model import SessionTranscriptModel


class SessionModel:
    def __init__(self, db, id=None, name=None, game=None, judge=None, summary=None):
        self.db = db
        self.id = id
        self.name = name
        self.game = game
        self.judge = judge
        self.summary = summary


    @classmethod
    def get_all(cls, db):
        query = "SELECT id, name, game, judge, summary FROM sessions;"
        results = db.fetch_results(query)
        sessions = []
        for row in results:
            sessions.append(cls(db, row[0], row[1], row[2], row[3], row[4]))
        return sessions

    @classmethod
    def get(cls, db, id):
        query = "SELECT id, name, game, judge, summary FROM sessions WHERE id = %s;"
        result = db.fetch_results(query, (id,))
        if result:
            row = result[0]
            return cls(db, row[0], row[1], row[2], row[3], row[4])
        return None

    def save(self):
        if self.id:
            # Update an existing session
            query = """
            INSERT INTO sessions (id, name, game, judge, summary)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            game = VALUES(game),
            judge = VALUES(judge),
            summary = VALUES(summary);
            """
            self.db.execute_query(
                query,
                (self.id, self.name, self.game, self.judge, self.summary)
            )
        else:
            # Insert a new session and retrieve the auto-incremented id
            query = """
            INSERT INTO sessions (name, game, judge, summary)
            VALUES (%s, %s, %s, %s);
            """
            self.id = self.db.execute_query(
                query,
                (self.name, self.game, self.judge, self.summary),
                return_last_insert_id=True
            )

    def delete(self):
        if self.id:
            SessionHistoryModel.delete_by_session_id(self.db, self.id)
            SessionPlayerModel.delete_by_session_id(self.db, self.id)
            SessionSettingModel.delete_by_session_id(self.db, self.id)
            SessionTranscriptModel.delete_by_session_id(self.db, self.id)
            PageModel.delete_by_session_id(self.db, self.id)

            query = "DELETE FROM sessions WHERE id = %s;"
            self.db.execute_query(query, (self.id,))

    def delete_players(self):
        query = "DELETE FROM session_players WHERE session_id = %s;"
        self.db.execute_query(query, (self.id,))

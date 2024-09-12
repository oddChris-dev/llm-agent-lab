import mysql.connector
from mysql.connector import Error

from systems.config import Config
import time
import threading


class Database:
    _connection = None
    _cursor = None
    _max_retries = 3
    _retry_delay = 2  # seconds
    _lock = threading.Lock()  # Lock for thread safety

    @classmethod
    def connect(cls):
        with cls._lock:
            if cls._connection is not None and cls._connection.is_connected():
                return  # Already connected

            config = Config()
            for attempt in range(cls._max_retries):
                try:
                    cls._connection = mysql.connector.connect(
                        host=config.db_host,
                        user=config.db_user,
                        port=config.db_port,
                        password=config.db_password,
                        database=config.db_database,
                        use_unicode=False
                    )
                    cls._cursor = cls._connection.cursor()
                    cls._cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;")

                    print("Connected to MySQL database")
                    break  # Break the loop if connection is successful
                except Error as ex:
                    print(f"Error connecting to MySQL (attempt {attempt + 1}): {ex}")
                    cls._connection = None
                    cls._cursor = None
                    if attempt < cls._max_retries - 1:  # Wait before retrying
                        time.sleep(cls._retry_delay)
                    else:
                        raise Exception("Max retries reached. Could not connect to MySQL database.")

    @classmethod
    def reconnect(cls):
        """Re-establish the database connection."""
        with cls._lock:
            print("Attempting to reconnect to the database...")
            cls.close()
            cls.connect()

    @classmethod
    def execute_query(cls, query, params=None, return_last_insert_id=False):
        with cls._lock:
            if cls._cursor is None:
                cls.connect()
            try:
                cls._cursor.execute(query, params or ())
                cls._connection.commit()
                if return_last_insert_id:
                    return cls._cursor.lastrowid
            except Error as ex:
                print(f"Error executing query: {ex}")
                if ex.errno in (2006, 2013, 2014, 2047, 2055):  # MySQL server has gone away or lost connection
                    cls.reconnect()
                    return cls.execute_query(query, params, return_last_insert_id)
                cls._connection.rollback()
                return None
            except Exception as ex:
                print(f"execute_query exception {ex} for {query}")
                cls._connection.rollback()
                return None
            return None

    @classmethod
    def fetch_results(cls, query, params=None, binary=False):
        with cls._lock:
            if cls._cursor is None:
                cls.connect()
            try:
                cls._cursor.execute(query, params or ())
                results = cls._cursor.fetchall()

                if not binary:
                    # Decode bytes to strings
                    decoded_results = []
                    for row in results:
                        decoded_row = tuple(
                            column.decode('utf-8') if isinstance(column, bytes) else column for column in row
                        )
                        decoded_results.append(decoded_row)
                    return decoded_results

                return results

            except Error as ex:
                print(f"Error fetching results: {ex}")
                if ex.errno in (2006, 2013, 2014, 2047, 2055):  # MySQL server has gone away or lost connection
                    cls.reconnect()
                    return cls.fetch_results(query, params, binary)
                return []
            except Exception as ex:
                print(f"fetch_results exception {ex} during query {query}")
                return []

    @classmethod
    def close(cls):
        with cls._lock:
            if cls._cursor:
                cls._cursor.close()
                cls._cursor = None
            if cls._connection:
                cls._connection.close()
                cls._connection = None

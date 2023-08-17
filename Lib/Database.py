import sqlite3

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('hashes.db')
        self.cursor = self.conn.cursor()

    def get_last_hash(self):
        last_hash_query = "SELECT hash FROM blockchain ORDER BY id DESC LIMIT 1"
        self.cursor.execute(last_hash_query)
        row = self.cursor.fetchone()
        if row:
            return row[0]
        else:
            return None

    def valid_hash(self, file_name, hash):
        query = "SELECT * FROM blockchain WHERE name = ? AND hash = ?"
        self.cursor.execute(query, (file_name, hash))
        result = self.cursor.fetchone()
        return result is not None

    def insert(self, filename, prev_hash, current_hash ):
        insert_query = "INSERT INTO blockchain (name, prev_hash, hash) VALUES (?, ?, ?)"
        data = (filename, prev_hash, current_hash)
        self.cursor.execute(insert_query, data)
        self.conn.commit()

    def select_all(self):
        select_query = "SELECT * FROM blockchain"
        self.cursor.execute(select_query)
        rows = self.cursor.fetchall()
        return rows

    def __del__(self):
        self.conn.close()
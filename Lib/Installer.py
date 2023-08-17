import sqlite3
import os

class Installer:
    def __init__(self):
        self.conn = sqlite3.connect('hashes.db')
        self.cursor = self.conn.cursor()

    def exec(self):
        # Create Database
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS blockchain (
        id INTEGER PRIMARY KEY,
        name TEXT,
        prev_hash TEXT,
        hash TEXT)''')

        # Create Folder
        os.makedirs("Frame")

    def __del__(self):
        self.conn.close()
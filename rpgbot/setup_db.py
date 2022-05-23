import os
import sqlite3 as sql
from dotenv import load_dotenv

load_dotenv()

con = sql.connect(os.getenv('DB_FILENAME'))

with con:
    con.execute(f"""
        CREATE TABLE {os.getenv('USER_TABLENAME')} (
            id INTEGER NOT NULL PRIMARY KEY,
            name TEXT
        );
    """)
    con.execute(f"""
        CREATE TABLE {os.getenv('CHARACTER_TABLENAME')} (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            owner TEXT,
            name TEXT,
            str INTEGER, dex INTEGER, con INTEGER, int INTEGER, wis INTEGER, cha INTEGER
        );
    """)
    con.execute(f"""
        CREATE TABLE {os.getenv('GAMEMODE_TABLENAME')} (
            id INTEGER NOT NULL PRIMARY KEY,
            value TEXT
        );
    """)
    con.commit()

msg = f"INSERT INTO {os.getenv('USER_TABLENAME')} (id, name) values(?, ?)"
data = [
    (165885524580630528, 'lowerlight'),
]
with con:
    con.executemany(msg, data)
    con.commit()

msg = f"""
    INSERT INTO {os.getenv('CHARACTER_TABLENAME')} (id, owner, name, str, dex, con, int, wis, cha) 
    values(?, ?, ?, ?, ?, ?, ?, ?, ?)
"""
data = [
    (1, 165885524580630528, 'Balls', 8, 9, 10, 11, 12, 13),
    (2, 165885524580630528, 'Spindle', 13, 12, 11, 10, 9, 8),
]
with con:
    con.executemany(msg, data)
    con.commit()

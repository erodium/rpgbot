import sqlite3 as sql
import configparser


def setup_db(config=None):
    if not config:
        config = configparser.ConfigParser()
        config.read('config.ini')
    
    con = sql.connect(config['db']['filename'])
    
    with con:
        con.execute(f"""
            CREATE TABLE {config['db-tables']['users']} (
                id INTEGER NOT NULL PRIMARY KEY,
                name TEXT
            );
        """)
        con.execute(f"""
            CREATE TABLE {config['db-tables']['characters']} (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                owner TEXT,
                name TEXT,
                str INTEGER, dex INTEGER, con INTEGER, int INTEGER, wis INTEGER, cha INTEGER
            );
        """)
        con.execute(f"""
            CREATE TABLE {config['db-tables']['gamemode']} (
                id INTEGER NOT NULL PRIMARY KEY,
                value TEXT
            );
        """)
        con.commit()
    
    msg = f"INSERT INTO {config['db-tables']['users']} (id, name) values(?, ?)"
    data = [
        (165885524580630528, 'lowerlight'),
    ]
    with con:
        con.executemany(msg, data)
        con.commit()
    
    msg = f"""
        INSERT INTO {config['db-tables']['characters']} (id, owner, name, str, dex, con, int, wis, cha) 
        values(?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    data = [
        (1, 165885524580630528, 'Balls', 8, 9, 10, 11, 12, 13),
        (2, 165885524580630528, 'Spindle', 13, 12, 11, 10, 9, 8),
    ]
    with con:
        con.executemany(msg, data)
        con.commit()

    msg = f"INSERT INTO {config['db-tables']['gamemode']} (id, value) values(?, ?)"
    data = [
        (1, 'downtime'),
    ]
    with con:
        con.executemany(msg, data)
        con.commit()
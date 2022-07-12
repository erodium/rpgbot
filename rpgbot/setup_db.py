import configparser
import sqlite3 as sql
from config import ROOT_DIR, CONFIG_FILENAME, DB_PATH
from utils import db_name


def setup_db(config=None):
    if not config:
        config = configparser.ConfigParser()
        config.read(CONFIG_FILENAME)
    con = sql.connect(DB_PATH / db_name(config))

    with con:
        con.execute(f"""
            CREATE TABLE {config['db-tables']['users']} (
                id INTEGER NOT NULL PRIMARY KEY,
                name TEXT
            );
        """)
        con.execute(f"""
            CREATE TABLE {config['db-tables']['characters']} (
                id TEXT NOT NULL PRIMARY KEY,
                owner TEXT,
                name TEXT,
                raw_json TEXT,
                class TEXT,
                level INTEGER,
                ancestry TEXT,
                heritage TEXT,
                background TEXT,
                alignment TEXT,
                gender TEXT,
                age TEXT,
                deity TEXT,
                keyability TEXT,
                languages TEXT,
                ancestryhp INTEGER, classhp INTEGER, bonushp INTEGER, bonushpPerLevel INTEGER, 
                speed INTEGER, speedBonus INTEGER,
                str INTEGER, dex INTEGER, con INTEGER, int INTEGER, wis INTEGER, cha INTEGER,
                classDC INTEGER, 
                perception INTEGER, fortitude INTEGER, reflex INTEGER, will INTEGER, 
                heavy INTEGER, medium INTEGER, light INTEGER, unarmored INTEGER, 
                advanced INTEGER, martial INTEGER, simple INTEGER, unarmed INTEGER, 
                castingArcane INTEGER, castingDivine INTEGER, castingOccult INTEGER, castingPrimal INTEGER, 
                acrobatics INTEGER, arcana INTEGER, athletics INTEGER, crafting INTEGER, deception INTEGER, 
                diplomacy INTEGER, intimidation INTEGER, medicine INTEGER, nature INTEGER, occultism INTEGER, 
                performance INTEGER, religion INTEGER, society INTEGER, stealth INTEGER, survival INTEGER, 
                thievery INTEGER, 
                acProfBonus INTEGER, acAbilityBonus INTEGER, acItemBonus INTEGER, acTotal INTEGER,
                active INTEGER
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
        INSERT INTO {config['db-tables']['characters']} (id, owner, name, str, dex, con, int, wis, cha, active) 
        values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    data = [
        ("165885524580630528_Balls", 165885524580630528, 'Balls', 8, 9, 10, 11, 12, 13, 1),
        ("165885524580630528_Spindle", 165885524580630528, 'Spindle', 13, 12, 11, 10, 9, 8, 0),
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

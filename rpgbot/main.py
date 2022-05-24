import os
import discord
import logging
from dotenv import load_dotenv
import d20
import sqlite3 as sql
import configparser
from setup_db import setup_db
from pathlib import Path
from random import randrange
import requests


def connect_to_db(config):
    dbfile = config['db']['filename']
    logger.info(f"Connecting to database at {dbfile}.")
    con = sql.connect(dbfile)
    return con


def get_greeting():
    greeting = ""
    with open('../assets/greetings.txt') as f:
        lines = f.readlines()
        total_lines = len(lines)
        linenum = randrange(total_lines)
        greeting = lines[linenum]
    return greeting


def check_pathbuilder_json_uri(content):
    parts = content.split()
    uri = parts[1]
    url = uri.split("?")[0]
    if url == 'https://pathbuilder2e.com/json.php':
        return uri
    return False


class RPGBot(discord.Client):
    def __init__(self, *args, **kwargs):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        p = Path(self.config['db']['filename'])
        if not p.exists():
            setup_db(self.config)
        self.con = connect_to_db(self.config)
        self.game_mode = self.get_game_mode_from_db()
        print(f"Setting game mode to {self.game_mode}.")
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents, *args, **kwargs)

    def change_game_mode(self, new_mode=None):
        if new_mode:
            old = self.game_mode
            logger.info(f"Changing game mode from {old} to {new_mode}")
            self.game_mode = new_mode
            q = f"UPDATE {self.config['db-tables']['gamemode']} SET value='{new_mode}' where id=1;"
            with self.con:
                self.con.execute(q)
            self.con.close()

    async def on_ready(self):
        print(f"We have logged in as {self.user}")

    async def on_message(self, message):
        if message.author == self.user:
            return
        ###
        # Check for $action commands
        ###
        if message.content.startswith('$'):
            if message.content.startswith('$hello'):
                greeting = get_greeting().replace("$USER$", message.author.display_name)
                logger.info(f"Greeting: {greeting}")
                await message.channel.send(greeting)
            elif message.content.startswith('$list'):
                print('list')
            elif message.content.startswith('$register'):
                valid_uri = check_pathbuilder_json_uri(message.content)
                if valid_uri:
                    uid = message.author.id
                    result = self.register_character(uid, valid_uri)

                    resp = requests.get(valid_uri, headers={"User-Agent": self.config['DEFAULT']['user_agent']})
                    resp.raise_for_status()
                    char_json = resp.json()
                    print(char_json)
                print('register')
            elif message.content.startswith('$r') or message.content.startswith('$roll'):
                to_roll = message.content.split()[1]
                result = d20.roll(to_roll)
                await message.channel.send(result)
        ###
        # Check for !meta commands
        ###
        elif message.content.startswith('!'):
            if message.content.startswith('!help'):
                with open('../assets/help.txt') as f:
                    msg = f.read()
                await message.author.send(msg)
            elif message.content.startswith('!m') or message.content.startswith('!mode'):
                parts = message.content.split()
                if len(parts) > 1:
                    mode = parts[1]
                    if mode in ['encounter', 'exploration', 'downtime']:
                        old = self.game_mode
                        self.change_game_mode(mode)
                        await message.channel.send(f'The game mode is now changed from {old} to {mode}.')
                else:
                    await message.channel.send(f'Current game mode is: {self.game_mode}')

    def get_game_mode_from_db(self):
        with self.con:
            q = f"SELECT value FROM {self.config['db-tables']['gamemode']} WHERE id=1;"
            val = self.con.execute(q).fetchone()[0]
            return val

    def register_character(self, uid, valid_uri):
        print(f'using {valid_uri} to register character to user {uid}')
        with self.con:
            q = f""


logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

load_dotenv()
bot = RPGBot()
bot.run(os.getenv('TOKEN'))

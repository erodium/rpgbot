import os
import discord
import logging
from dotenv import load_dotenv
import d20
import sqlite3 as sql


def connect_to_db():
    con = sql.connect(os.getenv('DB_FILENAME'))
    return con


class RPGBot(discord.Client):
    def __init__(self, *args, **kwargs):
        self.con = connect_to_db()
        self.game_mode = self.get_game_mode_from_db()
        print(f"Setting game mode to {self.game_mode}.")
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents, *args, **kwargs)

    def change_game_mode(self, new_mode=None):
        if new_mode:
            self.game_mode = new_mode
            q = f"UPDATE {os.getenv('GAMEMODE_TABLENAME')} SET value={new_mode} where ID=1;"
            with self.con:
                self.con.execute(q)
            self.con.close()

    async def on_ready(self):
        print(f"We have logged in as {self.user}")

    async def on_message(self, message):
        if message.author == self.user:
            return

        ###
        # Check for $meta commands
        ###
        if message.content.startswith('$'):
            if message.content.startswith('$hello'):
                await message.channel.send('Hello!')
            elif message.content.startswith('$register'):
                print('register')
            elif message.content.startswith('$list'):
                print('list')
        ###
        # Check for normal slash-type actions
        ###
        elif message.content.startswith('/'):
            if message.content.startswith('/r') or message.content.startswith('/roll'):
                to_roll = message.content.split()[1]
                result = d20.roll(to_roll)
                await message.channel.send(result)
        ###
        # Check for !action commands
        ###
        elif message.content.startswith('!'):
            if message.content.startswith('!m') or message.content.startswith('!mode'):
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
            q = f"SELECT value FROM {os.getenv('GAMEMODE_TABLENAME')} WHERE id=1;"
            val = self.con.execute(q).fetchone()[0]
            return val


logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

load_dotenv()
bot = RPGBot()
bot.run(os.getenv('TOKEN'))

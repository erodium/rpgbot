from __future__ import annotations

import configparser
import json
import logging
import os
import sqlite3 as sql
from random import randrange

import d20
import discord
import requests
from dotenv import load_dotenv

from rpgbot.aws import get_foundry_status
from rpgbot.aws import get_secret
from rpgbot.aws import turn_off_foundry
from rpgbot.aws import turn_on_foundry
from rpgbot.constants import ASSETS_PATH
from rpgbot.constants import CONFIG_FILENAME
from rpgbot.constants import DB_PATH
from rpgbot.constants import LIST_OF_CHECKS
from rpgbot.constants import LOG_PATH
from rpgbot.setup_db import setup_db
from rpgbot.utils import db_name


def check_pathbuilder_json_uri(uri):
    pb_url = 'https://pathbuilder2e.com/json.php'
    if len(uri) <= 6:
        try:
            int(uri)
        except ValueError:
            return False
        else:
            return f'{pb_url}?id={uri}'
    else:
        url = uri.split('?')[0]
        params = uri.split('?')[1]
        param = params.split('=')[0]
        if url == pb_url and param == 'id':
            return uri
    return False


def connect_to_db(config):
    dbfilename = db_name(config)
    logger.info(f'Connecting to database at {DB_PATH}/{dbfilename}.')
    con = sql.connect(DB_PATH / dbfilename)
    return con


def get_greeting():
    greeting = ''
    with open(ASSETS_PATH / 'greetings.txt') as f:
        lines = f.readlines()
        total_lines = len(lines)
        linenum = randrange(total_lines)
        greeting = lines[linenum]
    return greeting


def get_quote():
    with open(ASSETS_PATH / 'quotes.txt') as f:
        lines = f.readlines()
        total_lines = len(lines)
        linenum = randrange(total_lines)
        quote = lines[linenum]
    return quote


class RPGBot(discord.Client):
    def __init__(self, **kwargs):
        self.config = configparser.ConfigParser()
        self.config.read(CONFIG_FILENAME)
        p = DB_PATH / db_name(self.config)
        if not p.exists():
            setup_db(self.config)
        self.con = connect_to_db(self.config)
        self.game_mode = self.get_game_mode_from_db()
        print(f'Setting game mode to {self.game_mode}.')
        intents = discord.Intents.default()
        intents.message_content = True
        if self.config['secret']['location'] == 'aws':
            self.token = get_secret()
        elif self.config['secret']['location'] == 'env':
            load_dotenv()
            self.token = os.getenv('TOKEN')
        else:
            raise Exception('Invalid secret location')
        super().__init__(intents=intents, **kwargs)

    def change_game_mode(self, new_mode=None):
        if new_mode:
            old = self.game_mode
            logger.info(f'Changing game mode from {old} to {new_mode}')
            self.game_mode = new_mode
            q = f"UPDATE {self.config['db-tables']['gamemode']} SET value='{new_mode}' where id=1;"
            with self.con:
                self.con.execute(q)

    async def on_ready(self):
        print(f'We have logged in as {self.user}')

    async def on_message(self, message):
        if message.author == self.user:
            return
        ###
        # Check for $action commands
        ###
        if message.content.startswith('$'):
            if message.content.startswith('$activate'):
                parts = message.content.split()
                if len(parts) > 1:
                    result, retmsg = self.activate_character(
                        ' '.join(parts[1:]), message.author.id,
                    )
                    if result:
                        await message.channel.send(f'{" ".join(parts[1:])} is now your active character.')
                    else:
                        if retmsg == 'CannotFind':
                            msg = "Can't find that character in the database."
                        elif retmsg == 'AlreadyActive':
                            msg = 'That character is already active.'
                        elif retmsg == 'NoChars':
                            msg = "You don't have any registered characters."
                        else:
                            msg = f"Something went wrong. I couldn't make {' '.join(parts[1:])} your active character."
                        await message.channel.send(msg)
                else:
                    await message.channel.send('Which character do you want to activate?')
            elif message.content == '$active':
                result = self.get_active_char_from_db(message.author.id)
                if result:
                    await message.channel.send(f'{result} is your currently active character.')
                else:
                    await message.channel.send("You don't currently have an active character.")
            elif message.content.startswith('$char '):
                parts = message.content.split()
                active_char_name = self.get_active_char_from_db(
                    message.author.id,
                )
                result = self.get_character_info(
                    message.author.id, active_char_name, parts[1],
                )
                if result:
                    await message.channel.send(f"{active_char_name}'s {parts[1]} info: {result}")
                else:
                    await message.channel.send(f"Couldn't find {parts[1]} for {active_char_name}")
            elif message.content.startswith('$check '):
                parts = message.content.split()
                if parts[1] in LIST_OF_CHECKS:
                    result = self.roll_check(message.author.id, parts[1])
                    await message.channel.send(result)
            elif message.content == '$flat':
                active_char_name = self.get_active_char_from_db(
                    message.author.id,
                )
                self.flatten_character(message.author.id, active_char_name)
            elif message.content.startswith('$foundry '):
                parts = message.content.split()
                if parts[1] == 'start':
                    if get_foundry_status() != 'running':
                        await message.channel.send('Starting Foundry. This could take a minute.')
                        resp = turn_on_foundry()
                    else:
                        resp = 'Foundry is already running.'
                elif parts[1] == 'status':
                    stat = get_foundry_status()
                    resp = f'The Foundry instance is currently {stat}'
                elif parts[1] == 'stop':
                    if get_foundry_status() == 'running':
                        await message.channel.send('Stopping Foundry')
                        resp = turn_off_foundry()
                    else:
                        resp = 'The Foundry instance is not running.'
                else:
                    resp = 'The only supported options are `start`, `stop`, or `status`.'
                await message.channel.send(resp)
            elif message.content == '$hello' \
                    or message.content.startswith('$hello '):
                greeting = get_greeting().replace('$USER$', message.author.display_name)
                logger.info(f'Greeting: {greeting}')
                await message.channel.send(greeting)
            elif message.content == '$help':
                p = ASSETS_PATH / 'help.txt'
                q = ASSETS_PATH / 'changelog.txt'
                msg = p.read_text() + '\n' + q.read_text()
                await message.author.send(msg)
            elif message.content.startswith('$help '):
                pass
                # placeholder for subcommand help
            elif message.content == '$json':
                active_char_name = self.get_active_char_from_db(
                    message.author.id,
                )
                if active_char_name:
                    result = self.get_char_json(
                        message.author.id, active_char_name,
                    )
                    await message.channel.send(json.dumps(result)[0:2000])
                else:
                    await message.channel.send("You don't have an active character.")
            elif message.content == '$list':
                characters = self.get_characters_from_db(message.author.id)
                if len(characters) == 0:
                    msg = 'You have no characters in the database. Please $register one.'
                else:
                    msg = ''
                    for character_name, active in characters:
                        msg += f'* {character_name}'
                        if active:
                            msg += ' (Active)\n'
                        else:
                            msg += ' \n'
                await message.channel.send(msg)
            elif message.content.startswith('$mode'):
                parts = message.content.split()
                if len(parts) > 1:
                    mode = parts[1]
                    if mode in ['encounter', 'exploration', 'downtime']:
                        old = self.game_mode
                        self.change_game_mode(mode)
                        await message.channel.send(f'The game mode is now changed from {old} to {mode}.')
                elif message.content == '$mode':
                    await message.channel.send(f'Current game mode is: {self.game_mode}')
            elif message.content == '$quote':
                quote = get_quote()
                logger.info(f'Quote: {quote}')
                await message.channel.send(quote)
            elif message.content.startswith('$register '):
                parts = message.content.split()
                valid_uri = check_pathbuilder_json_uri(parts[1])
                if valid_uri:
                    uid = message.author.id
                    char_json = self.get_char_from_pb(valid_uri)
                    self.register_character(uid, char_json)
                    await message.channel.send(f"Character {char_json.get('name')} registered.")
                else:
                    await message.channel.send('Not a valid URL. Please check the !help and try again.')
            elif message.content.startswith('$roll ') or message.content.startswith('$r '):
                to_roll = message.content.split()[1]
                if any(i.isdigit() for i in to_roll):
                    result = d20.roll(to_roll)
                else:
                    result = self.roll_check(to_roll)
                await message.channel.send(result)
            elif message.content.startswith('$st '):
                parts = message.content.split()
                if parts[1] in ['will', 'ref', 'reflex', 'fort', 'fortitude']:
                    if parts[1] == 'ref':
                        f = 'reflex'
                    elif parts[1] == 'fort':
                        f = 'fortitude'
                    else:
                        f = parts[1]
                    result = self.roll_check(message.author.id, f)
                    await message.channel.send(result)

    def roll_check(self, author_id, field):
        active_char_name = self.get_active_char_from_db(author_id)
        mod = self.get_character_info(author_id, active_char_name, field)
        result = d20.roll(f'1d20+{mod}')
        return result

    def activate_character(self, char_name, owner_id):
        new_active_id = None
        with self.con:
            # Get all the owner's characters
            q = f"SELECT id, name, active FROM {self.config['db-tables']['characters']} WHERE owner={owner_id}"
            cur = self.con.execute(q)
            char_list = cur.fetchall()
            # if there aren't any owned characters
            if len(char_list) == 0:
                logger.debug(
                    f"Couldn't activate; found no characters in database for {owner_id}.",
                )
                return False, 'NoChars'  # no characters in list
            # for each character
            for character in char_list:
                # if we're looking at the current active character (1)
                if character[2] == 1:
                    # if the names match
                    if character[1] == char_name:
                        # then it's already active
                        return False, 'AlreadyActive'
                    # otherwise names don't match, so log the old active
                    old_active_id = character[0]
                # otherwise we're looking at a non active character
                # if this char is the desired active character
                if character[1] == char_name:
                    # log the id for the new active character
                    new_active_id = character[0]
            # if we didn't find the desired active character
            if not new_active_id:
                logger.debug(
                    f"Couldn't find the character {char_name} for {owner_id}.",
                )
                return False, 'CannotFind'  # can't find character name
            # otherwise we've found the character name
            q1 = f"UPDATE {self.config['db-tables']['characters']} SET active = 0 WHERE id='{old_active_id}';"
            self.con.execute(q1)
            logger.debug(f'successfully deactivated {old_active_id}.')
            q2 = f"UPDATE {self.config['db-tables']['characters']} SET active=1 WHERE id='{new_active_id}';"
            self.con.execute(q2)
            logger.debug(f'successfully activated {new_active_id}')
            return True, 'G2G'

    def flatten_character(self, owner_id, charname):
        char_json = self.get_char_json(owner_id, charname)
        cols = []
        vals = []
        for k, v in char_json.items():
            if isinstance(v, str):
                cols.append(k)
                vals.append(v)
            else:
                if k == 'languages':
                    cols.append(k)
                    vals.append(','.join(v))
                elif k in [
                    'attributes', 'abilities', 'proficiencies', 'acTotal',
                ]:
                    for k2, v2 in v.items():
                        cols.append(k2)
                        vals.append(v2)
        update_str = ','.join(
            [f"{cols[i]}='{vals[i]}'" for i in range(len(cols))],
        )
        with self.con:
            q = f"UPDATE {self.config['db-tables']['characters']} SET {update_str} WHERE id='{owner_id}_{charname}';"
            self.con.execute(q)

    def get_active_char_from_db(self, owner_id):
        with self.con:
            q = f"SELECT name FROM {self.config['db-tables']['characters']} WHERE owner={owner_id} AND active=1;"
            cur = self.con.execute(q)
            result = cur.fetchall()
            if len(result) == 0:
                return None
            elif len(result) > 1:
                raise f'Too many active for {owner_id}!'
            else:
                return result[0][0]

    def get_char_from_pb(self, valid_uri):
        logger.info(f'requesting character json from {valid_uri}')
        resp = requests.get(
            valid_uri, headers={
                'User-Agent': self.config['pathbuilder']['user_agent'],
            },
        )
        resp.raise_for_status()
        char_json = resp.json()
        if char_json['success']:
            logger.info(
                f'Successfully received character json from {valid_uri}',
            )
            return char_json.get('build')
        else:
            logger.error(f"Didn't get a successful json from {valid_uri}")
            return None

    def get_char_json(self, owner_id, active_char_name):
        with self.con:
            q = f"SELECT raw_json FROM {self.config['db-tables']['characters']} " \
                f"WHERE id='{owner_id}_{active_char_name};'"
            cur = self.con.execute(q)
            result = json.loads(cur.fetchone()[0])
        return result

    def get_character_info(self, owner_id, active_char_name, field):
        with self.con:
            q = f"SELECT {field} FROM {self.config['db-tables']['characters']} " \
                f"WHERE id='{owner_id}_{active_char_name}';"
            cur = self.con.execute(q)
            result = cur.fetchone()[0]
        return result

    def get_characters_from_db(self, owner_id):
        with self.con:
            q = f"SELECT name, active FROM {self.config['db-tables']['characters']} " \
                f'WHERE owner={owner_id};'
            cur = self.con.execute(q)
            chars = cur.fetchall()
        return chars

    def get_game_mode_from_db(self):
        with self.con:
            q = f"SELECT value FROM {self.config['db-tables']['gamemode']} " \
                f'WHERE id=1;'
            val = self.con.execute(q).fetchone()[0]
        return val

    def register_character(self, uid, char_json):
        logger.debug(f'Registering character to user {uid} from {char_json}')
        with self.con:
            char_name = char_json.get('name')
            obj_id = f'{uid}_{char_name}'
            q = f"REPLACE INTO {self.config['db-tables']['characters']} " \
                f'(id, owner, name, raw_json) ' \
                f"VALUES('{obj_id}', {uid}, '{char_name}', " \
                f"'{json.dumps(char_json)}');"
            self.con.execute(q)
            self.flatten_character(uid, char_name)


LOG_PATH.mkdir(exist_ok=True, parents=True)
logging.basicConfig(
    filename=LOG_PATH / 'rpgbot.log',
    filemode='w',
    level=logging.DEBUG,
    format='%(asctime)s:%(levelname)s:%(name)s: %(message)s',
)
logger = logging.getLogger(__name__)

bot = RPGBot()
bot.run(bot.token)

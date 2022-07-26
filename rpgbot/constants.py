from __future__ import annotations

from pathlib import Path

# Root Path
ROOT_DIR = Path(__file__).parents[1]

# Other Paths
ASSETS_PATH = ROOT_DIR / 'assets'
CONFIG_FILENAME = ROOT_DIR / 'config.ini'
DB_PATH = ROOT_DIR / 'data'
LOG_PATH = ROOT_DIR / 'logs'

# Other items
LIST_OF_CHECKS = [
    'perception', 'acrobatics', 'arcana', 'athletics', 'crafting', 'deception', 'diplomacy', 'intimidation',
    'medicine', 'nature', 'occultism', 'performance', 'religion', 'society', 'stealth', 'survival', 'thievery',
]

instance_id = 'i-0b77ab0785378a0eb'

from __future__ import annotations


def db_name(config):
    return f"{config['db']['stage']}-" \
           f"{config['db']['filename']}.{config['db']['ext']}"

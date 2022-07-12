def db_name(config):
    return f"{config['db']['stage']}-{config['db']['filename']}.{config['db']['ext']}"
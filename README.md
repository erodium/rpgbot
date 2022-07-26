1. The RPGbot will pull your Discord API key from one of two places: AWS or a .env file. Set this location in config.ini
   1. Either (AWS):
      1. Create an AWS Secrets Manager secret to hold your discord API key (with key of `token`).
      2. Place the Secret Name in `rpgbot/aws.py` under `get_secret.secret_name`.
      3. Ensure you have proper AWS credentials to retrieve the secret value.
   2. Or (.env):
      1. Create a .env file in the root directory.
      2. Add "TOKEN=YourSecretDiscordAPITokenString1231243124"
2. `pip install -r requirements.txt`
3. `python rpgbot/main.py`
4. Interact with the rpgbot via discord. See [assets/help.txt](./assets/help.txt) for commands.

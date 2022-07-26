1. Create an AWS Secrets Manager secret to hold your discord API key (with key of `token`).
2. Place the Secret Name in `rpgbot/aws.py` under `get_secret.secret_name`.
3. Ensure you have proper AWS credentials to retrieve the secret value.
4. `pip install -r requirements.txt`
5. `python rpgbot/main.py`
6. Interact with the rpgbot via discord. See [assets/help.txt](./assets/help.txt) for commands.

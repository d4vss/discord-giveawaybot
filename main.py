import os, disnake, dotenv, glob, sqlite3
from disnake.ext import commands
from helpers import db

bot = commands.InteractionBot(intents=disnake.Intents.all())
token = dotenv.get_key('.env', 'BOT_TOKEN')

print('='*10)
for filename in glob.glob('modules/**/*.py', recursive=True):
    n = filename.replace('\\', '.').replace('/', '.')
    if n.split('.')[2][0] != '~':
        bot.load_extension(n.replace('.py', ''))
        print('Loaded {}'.format(n.removeprefix('modules.')))
        continue

    print('Skipping {}'.format(n.removeprefix('modules.')))

sqlite3.connect(db.DATABASE_PATH)
bot.run(token)
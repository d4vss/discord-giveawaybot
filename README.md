# discord-giveawaybot
> A folder-module based Python Discord Giveaway Bot made with Disnake and Aiosqlite. Supports slash commands and util functions. 

## Disclaimer
To set this project up for your own purpose you will need python, pip and Discord related knowledge.

## Installation
1. Download and unzip the repository on the your side.
2. You will need a Discord account for the bot to work.
3. Create a new Discord Application on the [Discord Developer Page](https://discord.com/developers/applications). Press on the Bot tab and create a new bot. Copy the token.
4. Make sure to have all intents enabled. The bot won't work without all intents enabled.
5. Create a new .env file and paste the token as a string with `BOT_TOKEN` as key.
6. Install all needed libraries by running `pip install disnake aiosqlite python-dotenv humanize` on Windows and `pip3 install disnake aiosqlite python-dotenv humanize` on Linux.
7. Start the bot by running `python.exe main.py` on Windows or `python3 main.py` on Linux.

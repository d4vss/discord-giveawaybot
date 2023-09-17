import time
import asyncio
import random
import disnake
import re
from disnake.ext import commands, tasks
from disnake import Embed
from helpers import db

class EvalEvent(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.eval_loop.start()

    # Define a loop that runs every 15 seconds to evaluate giveaways
    @tasks.loop(seconds=15)
    async def eval_loop(self):
        # Fetch giveaways that have ended from the database
        giveaways = await db.fetch('giveaways', 'guild_id, channel_id, message_id, end_timestamp', True, f'WHERE end_timestamp <= {int(time.time())}')
        for giveaway in giveaways:
            try:
                # Fetch the associated guild, channel, and message
                guild = await self.bot.fetch_guild(giveaway[0])
                channel = await guild.fetch_channel(giveaway[1])
                message = await channel.fetch_message(giveaway[2])
            except:
                # If fetching fails (e.g., message or channel is deleted), delete the giveaway from the database
                return await db.delete('giveaways', f"WHERE message_id = {giveaway[2]}")

            # Fetch entries for the giveaway
            entries = await db.fetch('giveaway_entries', '*', True, f"WHERE message_id = {message.id}")
            if not entries:
                # If there are no entries, delete the giveaway and update its embed
                await db.delete('giveaways', f"WHERE message_id = {message.id}")

                embed = message.embeds[0]
                embed.description = re.sub(r'Ends in: <t:(\d+):R> \( <t:(\d+):F> \)', rf"Ended: <t:\1:F>", embed.description, 1, re.IGNORECASE)
                embed.description = re.sub(r'Winners: \*\*(\d+)\*\*', rf"Winners: **None**", embed.description, 1, re.IGNORECASE)
                embed.set_footer(text=f"{guild.name} - Bot by Davs", icon_url=(guild.icon.url if guild.icon else None))
                await message.edit(embed=embed, view=None)

                embed = Embed(description="**No one has entered the giveaway. :tada:**", color=0xffffff)
                embed.set_footer(text=f"{guild.name} - Bot by Davs", icon_url=(guild.icon.url if guild.icon else None))
                return await message.reply(embed=embed)
                

            matches = re.search(r'Winners: \*\*(\d+)\*\*', message.embeds[0].description)

            if matches:
                # Delete the giveaway from the database
                await db.delete('giveaways', f"WHERE message_id = {message.id}")
                winners_count = int(matches.group(1))
                
                if winners_count > len(entries):
                    winners_count = len(entries)
            
                winners = []
                for i in range(winners_count):
                    winner = random.choice(entries)
                    winners.append(winner[3])
                    entries.remove(winner)

                # Format winners as mentions
                winners = [f"<@{winner}>" for winner in winners]
                winners = ', '.join(winners)

                embed = message.embeds[0]
                embed.description = re.sub(r'Ends in: <t:(\d+):R> \( <t:(\d+):F> \)', rf"Ended: <t:\1:F>", embed.description, 1, re.IGNORECASE)
                embed.description = re.sub(r'Winners: \*\*(\d+)\*\*', rf"Winners: {winners}", embed.description, 1, re.IGNORECASE)
                embed.set_footer(text=f"{guild.name} - Bot by Davs", icon_url=(guild.icon.url if guild.icon else None))
                await message.edit(embed=embed, view=None)

                await message.reply(f"Congratulations to {winners}! You won the giveaway. :tada:")

    # Define a before_loop function to ensure the bot is ready before starting the loop
    @eval_loop.before_loop
    async def before_eval_loop(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(5)

# Define a function to set up the EvalEvent Cog
def setup(bot):
    bot.add_cog(EvalEvent(bot))

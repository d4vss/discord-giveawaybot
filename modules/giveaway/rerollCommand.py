import random
import disnake
import re
from disnake.ext import commands
from disnake import Embed
from helpers import db

# Define a Cog for rerolling giveaway winners
class RerollCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Rerolls a giveaway 🎉")
    async def greroll(self, inter, message_id = commands.Param(description="Message ID")):
        try:
            message_id = int(message_id)
        except:
            # Handle the case where the provided Message ID is invalid
            embed = Embed(description="**The message ID is invalid.**", color=0xffffff)
            return await inter.response.send_message(embed=embed, ephemeral=True)

        # Fetch giveaway entries for the specified message ID
        entries = await db.fetch('giveaway_entries', '*', True, f"WHERE message_id = {message_id}")
        if not entries:
            # Handle the case where the giveaway doesn't exist or has too few participants
            embed = Embed(description="**The giveaway does not exist or there are too few participants. :tada:**", color=0xffffff)
            embed.set_author(name=inter.guild.name, icon_url=inter.guild.icon.url)
            return await inter.response.send_message(embed=embed, ephemeral=True)

        # Retrieve information about the giveaway
        guild_id = entries[0][0]
        channel_id = entries[0][1]
        message_id = entries[0][2]
        user_id = entries[0][3]

        # Fetch the guild, channel, and message
        guild = await self.bot.fetch_guild(guild_id)
        channel = await guild.fetch_channel(channel_id)
        message = await channel.fetch_message(message_id)
        
        # Choose a random winner from the entries
        winner = random.choice(entries)

        # Update the giveaway message with the new winner
        embed = message.embeds[0]
        embed.description = re.sub(r'Ends in: <t:(\d+):R> \( <t:(\d+):F> \)', rf"Ended: <t:\1:F>", embed.description, 1, re.IGNORECASE)
        embed.description = re.sub(r'Winners: \*\*(\d+)\*\*', rf"Winners: <@{winner[3]}>", embed.description, 1, re.IGNORECASE)
        await message.edit(embed=embed, view=None)

        # Send a congratulatory message to the new winner
        await message.reply(f"Congratulations to <@{winner[3]}>! You have been redrawn. :tada:")

        # Send a confirmation message that the giveaway has been rerolled
        embed = Embed(description="**The giveaway has been rerolled.**", color=0xffffff)
        embed.set_footer(text=f"{inter.guild.name} - Bot by Davs", icon_url=(inter.guild.icon.url if inter.guild.icon else None))
        await inter.response.send_message(embed=embed, ephemeral=True)

# Define a function to set up the RerollCommand Cog
def setup(bot):
    bot.add_cog(RerollCommand(bot))

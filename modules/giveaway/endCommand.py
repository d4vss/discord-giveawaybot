import random
import disnake
import humanize
import re
from disnake.ext import commands
from disnake import Embed, ui, SelectOption
from datetime import datetime
from helpers import db

humanize.i18n.activate('en_US')

# Define a custom UI component for selecting giveaways
class GiveawaySelect(ui.StringSelect):
    def __init__(self, bot):
        self.bot = bot

        options = []

        # Fetch giveaway information from the database
        payload = db.dfetch('giveaways', 'guild_id, channel_id, message_id, end_timestamp, title', True)

        # Populate the options for the giveaway selection dropdown
        for giveaway in payload:
            guild_id, channel_id, message_id, end_timestamp, title = giveaway

            guild = self.bot.get_guild(guild_id)
            channel = guild.get_channel(channel_id)

            # Create a SelectOption for each giveaway and add it to the options list
            options.append(SelectOption(
                label=f"{title} - #{channel.name}",
                emoji="🎉",
                description=f"Endet: {humanize.naturaltime(datetime.now() - datetime.fromtimestamp(end_timestamp))}",
                value=f"{message_id}"
            ))

        # Initialize the StringSelect with the prepared options
        super().__init__(placeholder="Select a giveaway", options=options, min_values=1, max_values=1, custom_id="giveaway_select")

# Define a custom UI view for ending a giveaway
class GiveawayEnd(ui.View):
    def __init__(self, bot, message_id):
        self.bot = bot
        self.message_id = message_id

        super().__init__(timeout=None)

    # Define the "Beenden" button and its behavior
    @ui.button(label="End", style=disnake.ButtonStyle.red)
    async def end(self, button, inter):
        await inter.response.defer()

        # Fetch giveaway information from the database
        payload = await db.fetch('giveaways', 'guild_id, channel_id, message_id', False, f"WHERE message_id = {self.message_id}")

        # Delete the giveaway record from the database
        await db.delete('giveaways', f"WHERE message_id = {self.message_id}")

        # Fetch the guild, channel, and message objects for the giveaway
        guild = await self.bot.fetch_guild(payload[0])
        channel = await guild.fetch_channel(payload[1])
        message = await channel.fetch_message(payload[2])

        # Fetch entries for the giveaway
        entries = await db.fetch('giveaway_entries', '*', True, f"WHERE message_id = {message.id}")

        # Check if there are no entries in the giveaway
        if not entries:
            # Delete the giveaway and update its embed
            await db.delete('giveaways', f"WHERE message_id = {message.id}")
            embed = message.embeds[0]
            embed.description = re.sub(r'Ends in: <t:(\d+):R> \( <t:(\d+):F> \)', rf"Ended: <t:\1:F>", embed.description, 1, re.IGNORECASE)
            embed.description = re.sub(r'Winners: \*\*(\d+)\*\*', rf"Winners: **None**", embed.description, 1, re.IGNORECASE)
            embed.set_footer(text=f"{inter.guild.name} - Bot by Davs", icon_url=(inter.guild.icon.url if inter.guild.icon else None))

            # Edit the giveaway message and send a reply
            await message.edit(embed=embed, view=None)
            embed = Embed(description="**No one entered the giveaway. :tada:**", color=0xffffff)
            embed.set_footer(text=f"{inter.guild.name} - Bot by Davs", icon_url=(inter.guild.icon.url if inter.guild.icon else None))
            await message.reply(embed=embed)
            
            return await inter.delete_original_response()

        # Check for the "Gewinner: **(number)**" pattern in the giveaway description
        matches = re.search(r'Winners: \*\*(\d+)\*\*', message.embeds[0].description)

        if matches:
            await db.delete('giveaways', f"WHERE message_id = {message.id}")
            winners_count = int(matches.group(1))

            # Ensure winners_count does not exceed the number of entries
            if winners_count > len(entries):
                winners_count = len(entries)

            # Randomly select winners from the entries
            winners = []
            for i in range(winners_count):
                winner = random.choice(entries)
                winners.append(winner[3])
                entries.remove(winner)

            # Format winners as mentions
            winners = [f"<@{winner}>" for winner in winners]
            winners = ', '.join(winners)

            # Update the giveaway embed with winner information
            embed = message.embeds[0]
            embed.description = re.sub(r'Ends in: <t:(\d+):R> \( <t:(\d+):F> \)', rf"Ended: <t:\1:F>", embed.description, 1, re.IGNORECASE)
            embed.description = re.sub(r'Winners: \*\*(\d+)\*\*', rf"Winners: {winners}", embed.description, 1, re.IGNORECASE)
            embed.set_footer(text=f"{inter.guild.name} - Bot by Davs", icon_url=(inter.guild.icon.url if inter.guild.icon else None))

            # Edit the giveaway message with the updated embed
            await message.edit(embed=embed, view=None)

            # Send a congratulatory message to the winners
            await message.reply(f"Congratulations to {winners}! You won the giveaway. :tada:")

            await inter.delete_original_response()

# Define a cog for handling the "gend" (giveaway end) command
class EndCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Define a listener for dropdown interactions
    @commands.Cog.listener()
    async def on_dropdown(self, inter):
        if inter.component.custom_id == 'giveaway_select':
            await inter.response.defer()

            # Check if the selected giveaway exists in the database
            if not await db.fetch('giveaways', '*', False, f"WHERE message_id = {inter.values[0]}"):
                # If the giveaway doesn't exist, send an error message
                embed = Embed(description="**The giveaway does not exist.**", color=0xffffff)
                embed.set_footer(text=f"{inter.guild.name} - Bot by Davs", icon_url=(inter.guild.icon.url if inter.guild.icon else None))
                return await inter.send(embed=embed, view=None, ephemeral=True)

            # Confirm the user's intention to end the giveaway
            embed = Embed(description="**Are you sure you want to end the giveaway?**", color=0xffffff)
            embed.set_footer(text=f"{inter.guild.name} - Bot by Davs", icon_url=(inter.guild.icon.url if inter.guild.icon else None))

            # Edit the original interaction message to show the confirmation
            await inter.edit_original_message(embed=embed, view=GiveawayEnd(self.bot, inter.values[0]))

    # Define a slash command for ending a giveaway
    @commands.slash_command(description="Ends a giveaway. 🎉")
    @commands.has_permissions(administrator=True)
    async def gend(self, inter):
        # Check if there are any giveaways in the database
        if not await db.fetch('giveaways', '*', False):
            # If there are no giveaways, send a message indicating that
            embed = Embed(description="**There are no giveaways.**", color=0xffffff)
            embed.set_footer(text=f"{inter.guild.name} - Bot by Davs", icon_url=(inter.guild.icon.url if inter.guild.icon else None))
            return await inter.send(embed=embed, ephemeral=True)

        # Create an embed for the dropdown selection
        embed = Embed(description="**Select a giveaway.**", color=0xffffff)
        embed.set_footer(text=f"{inter.guild.name} - Bot by Davs", icon_url=(inter.guild.icon.url if inter.guild.icon else None))

        # Send the dropdown selection component with the embed
        await inter.send(components=GiveawaySelect(self.bot), embed=embed, ephemeral=True)

# Define a cog for the "EndCommand" commands and listeners
def setup(bot):
    bot.add_cog(EndCommand(bot))


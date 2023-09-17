import time
import disnake
import re
from disnake.ext import commands
from disnake import Embed, ui, TextInputStyle, ButtonStyle
from datetime import datetime
from helpers import db

# Define a modal for creating giveaways with various inputs
class GiveawayModal(ui.Modal):
    async def time_to_seconds(self, time_str):
        # Convert human-readable time duration to seconds
        parts = time_str.split()

        total_seconds = 0
        multiplier = 1
        
        unit_multipliers = {
            "second" : 1,
            "seconds" : 1,
            "minute" : 60,
            "minutes" : 60,
            "hour" : 3600,
            "hours" : 3600,
            "day" : 86400,
            "days" : 86400,
            "week" : 604800,
            "weeks" : 604800
        }
        
        matches = re.findall(r'(\d+)\s*([a-zA-Z]+)', time_str)

        total_seconds = 0

        for match in matches:
            number, unit = match
            multiplier = unit_multipliers.get(unit.lower())
            if multiplier is not None:
                total_seconds += int(number) * multiplier
            else:
                raise ValueError(f"Invalid unit: {unit}")

        return total_seconds

    def __init__(self):
        components = [
            ui.TextInput(
                label="Prize",
                placeholder="Enter the prize",
                custom_id="title",
                style=TextInputStyle.short,
                max_length=50,
            ),
            ui.TextInput(
                label="Description",
                placeholder="Enter the description (optional)",
                custom_id="description",
                style=TextInputStyle.paragraph,
                required=False,
            ),
            ui.TextInput(
                label="Winners",
                placeholder="Enter the number of winners",
                custom_id="winners",
                style=TextInputStyle.short,
                max_length=50,
            ),
            ui.TextInput(
                label="Duration",
                placeholder="Enter the duration",
                custom_id="duration",
                style=TextInputStyle.short,
                max_length=50,
            ),
        ]

        super().__init__(title='Create a giveaway', custom_id="create_giveaway", components=components)

    async def callback(self, inter):
        await inter.response.defer(ephemeral=True)
        title, description, winners, duration = inter.text_values.values()
        
        if not winners.isdigit() or int(winners) < 1:
            # If the number of winners is not a positive integer, send an error message
            embed = Embed(description="**The amount must be an number greater than 0.**", color=0xffffff)
            embed.set_footer(text=f"{inter.guild.name} - Bot by Davs", icon_url=(inter.guild.icon.url if inter.guild.icon else None))
            return await inter.send(embed=embed, view=None)

        try:
            # Convert the entered duration to seconds
            duration = await self.time_to_seconds(duration)
        except:
            # Handle incorrect time format input
            embed = Embed(description="**Wrong input.**", color=0xffffff)
            embed.set_footer(text=f"{inter.guild.name} - Bot by Davs", icon_url=(inter.guild.icon.url if inter.guild.icon else None))
            return await inter.send(embed=embed, view=None)

        # Create an embed for the giveaway
        embed = Embed(title=title, description=description, timestamp=datetime.fromtimestamp(int(time.time() + duration)), color=inter.guild.me.accent_color)
        embed.description += f"\n\Ends in: <t:{int(time.time() + duration)}:R> ( <t:{int(time.time() + duration)}:F> )\nHosted by: {inter.author.mention}\nEntrants: **0**\nWinners: **{winners}**"
        embed.set_footer(text=f"{inter.guild.name} - Bot by Davs", icon_url=(inter.guild.icon.url if inter.guild.icon else None))

        # Send the giveaway message with a "Join" button
        message = await inter.channel.send(embed=embed, view=GiveawayJoinButton())

        # Send a confirmation message with a link to the giveaway
        embed = Embed(description=f"**Giveaway is now live! [Go to the giveaway]({message.jump_url})**", color=0xffffff)
        embed.set_footer(text=f"{inter.guild.name} - Bot by Davs", icon_url=(inter.guild.icon.url if inter.guild.icon else None))
        await inter.edit_original_message(embed=embed, view=None)

        # Store the giveaway details in the database
        await db.insert('giveaways', 'guild_id, channel_id, message_id, end_timestamp, title', f"{inter.guild.id}, {inter.channel.id}, {message.id}, {int(time.time() + duration)}, '{title}'")

# Define a view for joining giveaways
class GiveawayJoinButton(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @ui.button(emoji="🎉")
    async def join(self, button, inter):
        # Check if the user has already joined the giveaway
        payload = await db.fetch('giveaway_entries', '*', False, f"WHERE message_id = {inter.message.id} AND user_id = {inter.author.id}")
        if payload:
            # If the user has already joined, send an error message
            embed = Embed(description="**:tada: You are already participating in this giveaway.**", color=0xffffff)
            embed.set_footer(text=f"{inter.guild.name} - Bot by Davs", icon_url=(inter.guild.icon.url if inter.guild.icon else None))
            return await inter.send(embed=embed, view=GivawayLeaveButton(inter.message.id), ephemeral=True)

        # Add the user to the giveaway entries in the database
        await db.insert('giveaway_entries', 'guild_id, channel_id, message_id, user_id', f"{inter.guild.id}, {inter.channel.id}, {inter.message.id}, {inter.author.id}")

        # Update the embed with the new participant count
        embed = inter.message.embeds[0]
        embed.description = re.sub(r'Entrants: \*\*(\d+)\*\*', rf"Entrants: **{len(await db.fetch('giveaway_entries', '*', True, f'WHERE message_id = {inter.message.id}'))}**", embed.description, 1, re.IGNORECASE)
        embed.set_footer(text=f"{inter.guild.name} - Bot by Davs", icon_url=(inter.guild.icon.url if inter.guild.icon else None))

        await inter.message.edit(embed=embed)
        await inter.response.defer()

# Define a view for leaving giveaways
class GivawayLeaveButton(ui.View):
    def __init__(self, message_id):
        super().__init__(timeout=None)
        self.message_id = message_id

    # ButtonStyle.red to indicate leaving
    @ui.button(label="Leave giveaway", style=ButtonStyle.red)
    async def leave(self, button, inter):
        await inter.response.defer(ephemeral=True)
        await db.delete('giveaway_entries', f"WHERE message_id = {self.message_id} AND user_id = {inter.author.id}")

        # Fetch the giveaway message and update the participant count in the embed
        message = await inter.channel.fetch_message(self.message_id)
        embed = message.embeds[0]
        embed.description = re.sub(r'Entrants: \*\*(\d+)\*\*', rf"Entrants: **{len(await db.fetch('giveaway_entries', '*', True, f'WHERE message_id = {inter.message.id}'))}**", embed.description, 1, re.IGNORECASE)
        
        await message.edit(embed=embed)

        # Send a confirmation message that the user has left the giveaway
        embed = Embed(description="**You've left this giveaway.**", color=0xffffff)
        embed.set_footer(text=f"{inter.guild.name} - Bot by Davs", icon_url=(inter.guild.icon.url if inter.guild.icon else None))
        await inter.edit_original_message(embed=embed, view=None)

# Define a Cog for creating giveaways
class CreateCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Create a giveaway. 🎉")
    @commands.has_permissions(administrator=True)
    async def gcreate(self, inter):
        await inter.response.send_modal(modal=GiveawayModal())

# Define a function to set up the CreateCommand Cog
def setup(bot):
    bot.add_cog(CreateCommand(bot))


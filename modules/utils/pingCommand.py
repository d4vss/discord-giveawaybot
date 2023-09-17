import time
from disnake.ext import commands
from disnake import Embed

class PingCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Returns the latency of the bot. 🏓️")
    async def ping(self, inter):
        # Record start time
        start_time = time.time()

        # Defer the response to avoid timeouts
        await inter.response.defer(ephemeral=True)

        # Record end time
        end_time = time.time()

        # Calculate latencies
        discord_ws_latency = round(self.bot.latency * 1000)
        bot_latency = round((end_time - start_time) * 1000)

        # Create and send embed
        embed = Embed(description=f"**Discord WS Latenz:** {discord_ws_latency}ms \n**Bot Latenz:** {bot_latency}ms", color=0xffffff)
        embed.set_footer(text=f"{inter.guild.name} - Bot by Davs", icon_url=(inter.guild.icon.url if inter.guild.icon else None))
        await inter.edit_original_message(embed=embed)

def setup(bot):
    bot.add_cog(PingCommand(bot))

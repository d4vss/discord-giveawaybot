import os
import glob
from disnake import Embed
from disnake.ext import commands

class ReloadCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Reloads all files. 🔄")
    # @commands.is_owner()
    async def reload(self, inter):
        success_count = 0
        reload_text = ""

        # Send initial response indicating reloading
        embed = Embed(description="**Reloading all files...**", color=0xffffff)
        embed.set_footer(text=f"{inter.guild.name} - Bot by Davs", icon_url=(inter.guild.icon.url if inter.guild.icon else None))
        await inter.send(embed=embed, ephemeral=True)
        print("Reloading all cogs...")

        # Loop through each .py file in the 'cogs' directory and its subdirectories
        for filename in glob.glob('modules/**/*.py', recursive=True):
            # Convert file path to dot-separated format for extension loading
            cog_path = os.path.splitext(filename)[0].replace(os.path.sep, '.')
            cog_name = cog_path.removeprefix('modules.')

            try:
                # Attempt to reload the extension
                self.bot.reload_extension(cog_path)
                print(f"Reloaded {cog_name}.py")
                reload_text += f":white_check_mark: - **{cog_name}**\n"
                success_count += 1
            except:
                try:
                    # If not loaded, load the extension
                    self.bot.load_extension(cog_path)
                    print(f"Loaded {cog_name}.py")
                    reload_text += f":new: - **{cog_name}**\n"
                    success_count += 1
                except Exception as e:
                    reload_text += f":x: - **{cog_name}**\n"

        # Indicate completion of reloading process
        print("Reloaded all cogs!\n" + "="*10)

        # Create and send an embed summarizing the results
        embed = Embed(description=f"**{success_count} out of {len(self.bot.cogs)} files were reloaded.**\n\n{reload_text}", color=0xffffff)
        embed.set_footer(text=f"{inter.guild.name} - Bot by Davs", icon_url=(inter.guild.icon.url if inter.guild.icon else None))

        await inter.edit_original_message(embed=embed)
        await inter.delete_original_response(delay=5)

def setup(bot):
    bot.add_cog(ReloadCommand(bot))

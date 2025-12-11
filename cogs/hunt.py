from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands

class Hunt(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot 

    @app_commands.command(
            name="hunt", 
            description="Hunt for monsters"
    )
    async def hunt(self, interaction:discord.Interaction):
        await interaction.response.send_message("Hunting for animals!")

async def setup(bot: commands.Bot):
    await bot.add_cog(Hunt(bot))
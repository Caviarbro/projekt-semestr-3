from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
from utils.util_file import get_user

class Hunt(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot 

    @app_commands.command(
            name="hunt", 
            description="Hunt for monsters"
    )
    async def hunt(self, interaction:discord.Interaction):
        try:
            user = await get_user(interaction.user.id)

            if (user is not None):
                await interaction.response.send_message("Hunting for animals!")
            else:
                raise ValueError("Missing user in database!")
        except Exception as e:
            await interaction.response.send_message(f"[ERROR]: While hunting, message: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Hunt(bot))
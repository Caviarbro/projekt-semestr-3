from __future__ import annotations
import discord, random
from discord import app_commands
from discord.ext import commands
from utils.util_file import get_user, get_config, save_monster

class Crate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot 

    @app_commands.command(
            name="crate", 
            description="Open for items"
    )
    async def crate(self, interaction:discord.Interaction):
        try:
            user = await get_user(interaction.user.id)

            if (user is not None):

                await interaction.response.send_message(f"You found following items:")
            else:
                raise ValueError("Missing user in database!")
        except Exception as e:
            await interaction.response.send_message(f"[ERROR]: While opening crate, message: {e}")

def generate_weapon(amount):
    config = get_config()

    weapon_List = config["weapons"]
    new_weapons = []

    # TODO
    for _ in range(0, amount):
        new_weapons = weapon_List[random.randrange(0, len(weapon_List))]   

        new_weapons.append(new_weapons)

    return new_weapons     

async def setup(bot: commands.Bot):
    await bot.add_cog(Crate(bot))
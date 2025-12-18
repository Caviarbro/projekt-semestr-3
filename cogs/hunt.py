from __future__ import annotations
import discord, random
from discord import app_commands
from discord.ext import commands
from utils.util_file import get_user, get_config, save_monster

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
                new_monsters = generate_monster(10)

                for monster in new_monsters:
                    print("MY MONSTER:", monster)
                    await save_monster(interaction.user.id, monster["type"])

                monster_emojis = [monster["emoji"] for monster in new_monsters]

                await interaction.response.send_message(f"Hunting for animals! {" ".join(monster_emojis)}")
            else:
                raise ValueError("Missing user in database!")
        except Exception as e:
            await interaction.response.send_message(f"[ERROR]: While hunting, message: {e}")

def generate_monster(amount):
    config = get_config()

    monster_list = config["monsters"]
    new_monsters = []

    for _ in range(0, amount):
        new_monster = monster_list[random.randrange(0, len(monster_list))]   

        new_monsters.append(new_monster)

    return new_monsters     

async def setup(bot: commands.Bot):
    await bot.add_cog(Hunt(bot))
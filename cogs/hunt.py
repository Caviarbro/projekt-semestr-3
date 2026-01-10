from __future__ import annotations
import discord, random, sys, traceback
from discord import app_commands
from discord.ext import commands
from utils.util_file import get_user, get_config, save_monster, get_cooldown, roll_quality, process_command_cost, get_setting

class Hunt(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot 

    @app_commands.command(
            name="hunt", 
            description="Hunt for monsters"
    )
    async def hunt(self, interaction:discord.Interaction):
        try:
            # defer the response because we are requesting from the database and the slash command may fail
            await interaction.response.defer()

            cooldown = await get_cooldown(interaction.user.id, interaction.command.name, set = True, message = True)

            if (cooldown):
                return await interaction.followup.send(content = cooldown)
            
            # user data check is inside of this function, so it doesn't make sense to call the function here as well
            not_enough_to_process = await process_command_cost(interaction.user.id, interaction.command.name)

            if (not_enough_to_process):
                return await interaction.followup.send(content = not_enough_to_process)
            
            MONSTERS_PER_HUNT = get_setting("monsters_per_hunt")
            new_monsters = generate_monster(MONSTERS_PER_HUNT)

            for monster in new_monsters:
                await save_monster(interaction.user.id, monster["type"])

            monster_emojis = [monster["emoji"] for monster in new_monsters]

            await interaction.followup.send(f"Hunting for monsters! {" ".join(monster_emojis)}")
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            line = exc_tb.tb_lineno

            full_traceback = ''.join(
                traceback.format_exception(exc_type, exc_obj, exc_tb)
            )

            print(f"ERROR while hunting: {full_traceback} at line: {line}")

            await interaction.followup.send(f"[ERROR]: While hunting, message: {e}")

def generate_monster(amount):
    config = get_config()

    monster_list = config["monsters"]
    new_monsters = []

    for _ in range(0, amount):
        generated_rarity = roll_quality(only_rarity = True)
        rarity_monster_list = [m for m in monster_list if m["rarity"] == generated_rarity]

        new_monster = rarity_monster_list[random.randrange(0, len(rarity_monster_list))]   

        new_monsters.append(new_monster)

    return new_monsters     

async def setup(bot: commands.Bot):
    await bot.add_cog(Hunt(bot))
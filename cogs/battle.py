from __future__ import annotations
import discord, random, sys
from discord import app_commands
from discord.ext import commands
from utils.util_file import get_user, get_config, get_team, get_active_team, get_emoji, get_rarity_info, get_level, save_team, xp_for_level, get_monster_stats, get_weapon_string, change_team, add_team_monster, remove_team_monster

class Battle(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot 

    battle_command = app_commands.Group(
            name="battle", 
            description="Battle related commands"
    )

    @battle_command.command(
        name = "battle",
        description = "Battle"
    )
    async def team_remove(self, interaction:discord.Interaction, user:discord.User = None):
        try:
            # defer the response because we are requesting from the database and the slash command may fail
            await interaction.response.defer()

            user_data = await get_user(interaction.user.id)

            if (user_data is not None):
                team_data, team_monsters = await get_active_team(interaction.user.id)

            else:
                raise ValueError("Missing user in database!")
        except Exception as e:
            await interaction.followup.send(f"[ERROR]: While battling, message: {e}")

class battle_team():
    def __init__(self, monsters, weapons):
        self.monsters = monsters
        self.weapons = weapons
        
async def create_battle_team_data(user_id):
    team_data, team_monsters = await get_active_team(user_id)

    battle_monsters = []
    battle_weapons = []
    
    for monster in team_monsters:
         [monster_data, monster_config, t_monster, weapon_data, weapon_config] = monster 



async def setup(bot: commands.Bot):
    await bot.add_cog(Battle(bot))
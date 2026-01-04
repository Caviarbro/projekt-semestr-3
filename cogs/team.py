from __future__ import annotations
import discord, random, sys, traceback
from discord import app_commands
from discord.ext import commands
from utils.util_file import get_user, get_config, get_team, get_active_team, get_emoji, get_rarity_info, get_level, save_team, xp_for_level, get_monster_stats, get_weapon_string, change_team, add_team_monster, remove_team_monster

class Team(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot 

    team_command = app_commands.Group(
            name="team", 
            description="Team related commands"
    )

    @team_command.command(
            name = "view",
            description = "View team"
    )
    async def team_view(self, interaction:discord.Interaction):
        try:
            # defer the response because we are requesting from the database and the slash command may fail
            await interaction.response.defer()

            user_data = await get_user(interaction.user.id)

            if (user_data is not None):
                # if user doesn't have any team
                if (len(user_data.t_ids) == 0):
                    await save_team(interaction.user.id)
                
                embed, team_number, user_team_ids = await show_page(interaction)

                await interaction.followup.send(embed = embed, view = InteractionHandler(team_number = team_number, user_team_ids = user_team_ids))
            else:
                raise ValueError("Missing user in database!")
        except Exception as e:
            await interaction.followup.send(f"[ERROR]: While viewing team, message: {e}")

    @team_command.command(
        name = "add",
        description = "Add monster team"
    )
    async def team_add(self, interaction:discord.Interaction, monster_name:str, position:int = None):
        try:
            # defer the response because we are requesting from the database and the slash command may fail
            await interaction.response.defer()

            user_data = await get_user(interaction.user.id)

            if (user_data is not None):
                await add_team_monster(interaction.user.id, monster_name, position)

                team_data, team_monsters = await get_active_team(interaction.user.id)

                for monster in team_monsters:
                    [monster_data, monster_config, t_monster, weapon_data, weapon_config] = monster 
                    
                    if (monster_config["name"].lower() == monster_name.lower()):
                        return await interaction.followup.send(f"{get_emoji('success')} {monster_config['emoji']} **{monster_config['name']}** added to position **[{t_monster.pos}]**!")
            else:
                raise ValueError("Missing user in database!")
        except Exception as e:
            await interaction.followup.send(f"[ERROR]: While adding to team, message: {e}")

    @team_command.command(
        name = "remove",
        description = "Remove monster from team"
    )
    async def team_remove(self, interaction:discord.Interaction, monster_name:str = None, position:int = None):
        try:
            # defer the response because we are requesting from the database and the slash command may fail
            await interaction.response.defer()

            if (monster_name is None and position is None):
                raise ValueError("At least one argument (monster_name / position) expected!")

            user_data = await get_user(interaction.user.id)

            if (user_data is not None):
                team_data, team_monsters = await get_active_team(interaction.user.id)

                for monster in team_monsters:
                    [monster_data, monster_config, t_monster, weapon_data, weapon_config] = monster 
                    
                    lowercase_monster_name = monster_name.lower() if monster_name is not None else ""

                    if (monster_config["name"].lower() == lowercase_monster_name or t_monster.pos == position):
                        await remove_team_monster(interaction.user.id, t_monster.pos)

                        return await interaction.followup.send(f"{get_emoji('delete')} {monster_config['emoji']} **{monster_config['name']}** was removed from position **[{t_monster.pos}]**!")
            else:
                raise ValueError("Missing user in database!")
        except Exception as e:
            await interaction.followup.send(f"[ERROR]: While removing from team, message: {e}")

    # TODO: add team naming
class InteractionHandler(discord.ui.View):
    def __init__(self, *, team_number, user_team_ids):
        super().__init__(timeout=120)
        config = get_config()

        self.user_team_ids = user_team_ids
        self.current_page = team_number
        self.max_teams_per_user = config["settings"]["max_teams_per_user"]

    async def refresh_page(self, interaction: discord.Interaction):
        # Fetch the current page embed and update the user_team_ids dynamically.
        print("current page", self.current_page)
        embed, team_number, user_team_ids = await show_page(interaction, self.current_page)
        self.user_team_ids = user_team_ids

        # clamp current page in case teams were removed
        self.current_page = min(self.current_page, len(self.user_team_ids) - 1)
        return embed

    # move to previous page
    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.secondary)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1

        if (self.current_page < 0):
            self.current_page = len(self.user_team_ids)

        embed = await self.refresh_page(interaction)
        await interaction.response.edit_message(embed=embed, view=self)

    # move to next page
    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            self.current_page += 1
            
            if (self.current_page >= self.max_teams_per_user):
                self.current_page = 0

            embed = await self.refresh_page(interaction)
            await interaction.response.edit_message(embed=embed, view = self)
        except Exception as e:
            await interaction.response.edit_message(content = e, embed = embed, view = self)

    # change active team
    @discord.ui.button(emoji="⭐", style=discord.ButtonStyle.primary)
    async def set_active(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await change_team(interaction.user.id, self.current_page)

            embed = await self.refresh_page(interaction)
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            line = exc_tb.tb_lineno

            print(f"ERROR {e} at line: {line}")

async def show_page(interaction : discord.Interaction, team_number = None):
    try:
        user_data = await get_user(interaction.user.id)

        if user_data is None:
            raise ValueError("No user to display team for!")

        team_data, team_monsters = (
            await get_active_team(interaction.user.id) if team_number is None else 
            await get_team(interaction.user.id, team_number = team_number, create_if_not_exist = True)
        )

        user_team_ids = user_data.t_ids
        team_number = user_team_ids.index(team_data.t_id) if team_number is None else team_number
        team_active = team_data.active

        # if team gets dynamically created add the new team id to the user_team_ids
        if (team_number > len(user_team_ids) - 1):
            user_team_ids.append(team_data.t_id)

        embed = discord.Embed(
            title = f"{'⭐' if team_active else get_emoji('error')} {interaction.user.name}'s Team!",
            color = discord.Color.dark_blue()
        )

        for monster in team_monsters:
            [monster_data, monster_config, t_monster, weapon_data, weapon_config] = monster 

            position_in_team = t_monster.pos
            monster_level = get_level(monster_data.xp)
            next_level_xp = xp_for_level(monster_level + 1)

            stat_emojis = get_emoji("stats")
            monster_stats = await get_monster_stats(interaction.user.id, monster_data.m_id)

            monster_stats = [round(stat) for stat in monster_stats]
            max_len = max(len(str(stat)) for idx, stat in enumerate(monster_stats) if not idx in [2,5]) # 2 is strength_defense and 5 is mag_defense, they have additional % after the numbers

            stats_padding = [
                str(stat).ljust(max_len) 
                for stat in monster_stats
            ]

            weapon_string = await get_weapon_string(interaction.user.id, weapon_data.w_id, "full") if (monster_data.e_wid != -1) else "No weapon"
            spacing = f"  "

            embed.add_field(
                name = f"[{position_in_team}] {monster_config['emoji']} {monster_config['name']}", 
                value = f"""Level **{monster_level}**
                [**{monster_data.xp}**/**{next_level_xp}**]
                > {stat_emojis[0]}**: `{stats_padding[0]}`**{spacing}{stat_emojis[3]}**: `{stats_padding[3]}`**
                > {stat_emojis[1]}**: `{stats_padding[1]}`**{spacing}{stat_emojis[4]}**: `{stats_padding[4]}`**
                > {stat_emojis[2]}**: `{monster_stats[2]}%`**{spacing}{stat_emojis[5]}**: `{monster_stats[5]}%`**
                {weapon_string}
                """
            )

        embed.set_footer(text = f"Team {team_number + 1} / {len(user_team_ids)} | Streak: {team_data.streak}")

        return embed, team_number, user_team_ids
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line = exc_tb.tb_lineno

        full_traceback = ''.join(
            traceback.format_exception(exc_type, exc_obj, exc_tb)
        )

        print("ERROR WHILE SHOWING", full_traceback, "at line:", line)

        raise ValueError(f"[ERROR]: While showing team, message: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Team(bot))
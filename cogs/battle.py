from __future__ import annotations
import discord, random, sys
from discord import app_commands
from discord.ext import commands
from utils.util_file import get_user, get_config, get_team, get_emoji, get_level, get_weapon_string, get_monster_config, get_setting, get_cooldown, set_cooldown
from battle_system.files.battle_util import execute_battle, Battle, create_from_team_data
from battle_system.files.battle_classes import BattleContext, BattleLog, BattleLogSnapshot, BattleLogEntry

class Battle(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot 

    @app_commands.command(
        name = "battle",
        description = "Battle with other teams!"
    )
    async def battle(self, interaction:discord.Interaction, user:discord.User = None, team_number : int = None):
        try:
            await interaction.response.defer()

            cooldown = await get_cooldown(interaction.user.id, interaction.command.name, set = True, message = True)

            if (cooldown):
                return await interaction.followup.send(content = cooldown)

            user_data = await get_user(interaction.user.id)

            if (not user_data):
                raise ValueError("Missing user in the database!")
            
            interact_allow_user_ids = []

            battle_result: Battle = None
            new_streak: int = None

            target_user_id = None
            target_team_data = None
            random_target = False
            count_streak = False

            interact_allow_user_ids.append(interaction.user.id)
            
            if (user):
                target_user_id = user.id
                interact_allow_user_ids.append(target_user_id)

            elif (team_number):
                team_number_zero_index = team_number - 1
                team_data, team_monsters = await get_team(
                    interaction.user.id,
                    team_number = team_number_zero_index
                )
                target_team_data = create_from_team_data(team_data, team_monsters)

            else:
                random_target = True
                count_streak = True

            battle_result, new_streak = await execute_battle(
                actor_user_id = interaction.user.id,
                target_user_id = target_user_id,
                target_team_data = target_team_data,
                random_target = random_target,
                count_streak = count_streak
            )

            view = InteractionHandler(
                battle_result,
                battle_result.battle_ctx.turn_number,
                user_ids = interact_allow_user_ids,
                streak = new_streak
            )

            embeds = await view.refresh_page(interaction)
            await interaction.followup.send(embeds = embeds, view = view)
        except Exception as e:
            await interaction.followup.send(f"[ERROR]: While battling, message: {e}")

class InteractionHandler(discord.ui.View):
    def __init__(self, battle_result, turn_number, *, user_ids, streak):
        super().__init__(timeout = 120)
        
        self.battle_result = battle_result
        self.current_page = turn_number
        self.max_battle_turns = battle_result.battle_ctx.turn_number
        self.user_ids = user_ids
        self.streak = streak
        self.show_logs = False
        
    async def refresh_page(self, interaction: discord.Interaction):
        # Fetch the current page embed and update the user_team_ids dynamically.
        embeds = []
        battle_embed = await show_page(self.battle_result, self.current_page, interaction = interaction, user_ids = self.user_ids, streak = self.streak)

        embeds.append(battle_embed)

        if (self.show_logs):
            log_embeds = show_logs(self.battle_result, self.current_page)

            embeds.extend(log_embeds)

        return embeds

    async def can_interact(self, interaction : discord.Interaction):
        is_able = True if interaction.user.id in self.user_ids else False 

        if (not is_able):
            await interaction.response.send_message(ephemeral = True, content = "You can't interact with this component!")

        return is_able
    
    # move five previous pages
    @discord.ui.button(emoji="⏪", style=discord.ButtonStyle.secondary)
    async def fast_prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        can_interact = await self.can_interact(interaction)

        if (not can_interact):
            return
        
        self.current_page -= 5

        if (self.current_page < 0):
            self.current_page = self.max_battle_turns

        embeds = await self.refresh_page(interaction)
        await interaction.response.edit_message(embeds = embeds, view=self)

    # move to previous page
    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.secondary)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        can_interact = await self.can_interact(interaction)

        if (not can_interact):
            return
        
        self.current_page -= 1

        if (self.current_page < 0):
            self.current_page = self.max_battle_turns

        embeds = await self.refresh_page(interaction)
        await interaction.response.edit_message(embeds = embeds, view=self)

    # move to next page
    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        can_interact = await self.can_interact(interaction)

        if (not can_interact):
            return
        
        self.current_page += 1
        
        if (self.current_page > self.max_battle_turns):
            self.current_page = 0

        embeds = await self.refresh_page(interaction)
        await interaction.response.edit_message(embeds = embeds, view = self)

    # move five pages next
    @discord.ui.button(emoji="⏩", style=discord.ButtonStyle.secondary)
    async def fast_next(self, interaction: discord.Interaction, button: discord.ui.Button):
        can_interact = await self.can_interact(interaction)

        if (not can_interact):
            return
        
        self.current_page += 5
        
        if (self.current_page > self.max_battle_turns):
            self.current_page = 0

        embeds = await self.refresh_page(interaction)
        await interaction.response.edit_message(embeds = embeds, view = self)

    # show logs
    @discord.ui.button(emoji="🗃️", style=discord.ButtonStyle.danger)
    async def logs(self, interaction: discord.Interaction, button: discord.ui.Button):
        can_interact = await self.can_interact(interaction)

        if (not can_interact):
            return
        
        self.show_logs = not self.show_logs

        if (self.show_logs):
            button.style = discord.ButtonStyle.success
        else:
            button.style = discord.ButtonStyle.danger

        embeds = await self.refresh_page(interaction)
        
        await interaction.response.edit_message(embeds = embeds, view = self)

def show_logs(battle_result : Battle, current_turn_number :int):
    battle_ctx : BattleContext = battle_result.battle_ctx
    turn_log : BattleLog  = battle_ctx.logs._get_turn_log(current_turn_number, create_new = False)

    actor_team = battle_ctx.actor_team
    target_team = battle_ctx.target_team

    description_texts = []

    for entry in turn_log["entries"]:
        entry : BattleLogEntry = entry 

        is_default_actor = True if (actor_team.get_monster(id = entry.actor_id)) else False 

        new_text = f"**[{'ACTOR' if is_default_actor else 'TARGET'}]:** {entry.result}\n"

        if (description_texts):
            if ((len(description_texts[-1]) + len(new_text)) <= 4096):
                description_texts[-1] += new_text
            else:
                description_texts.append(new_text)
        else:
            description_texts.append(new_text)
    
    if (not description_texts):
        description_texts.append("No logs for this turn!")

    embeds = []

    for index, description_text in enumerate(description_texts):
        embed = discord.Embed()

        if (index == 0):
            embed.title = f"Battle log [{current_turn_number + 1} / {battle_ctx.turn_number + 1}]"

        embed.description = description_text
        embed.color = discord.Colour.blue()

        embeds.append(embed)

    return embeds

async def show_page(battle_result : Battle, current_turn_number : int, *, interaction : discord.Interaction, user_ids : list[int] = [], streak : int):
    try:
        end_state = battle_result.end_state
        battle_ctx : BattleContext = battle_result.battle_ctx

        if (not end_state):
            raise ValueError("No battle end state found!")
        
        turn_log : BattleLog  = battle_ctx.logs._get_turn_log(current_turn_number, create_new = False)
        turn_snapshot : BattleLogSnapshot = turn_log["snapshots"]

        if (turn_snapshot):
            turn_snapshot = turn_snapshot[0]

        embed = discord.Embed()

        fetched_users : list[discord.User]= []

        if (len(user_ids) == 1):
            fetched_users.append(interaction.user)

            embed.set_author(name = f"{interaction.user.name}'s Monster battle", icon_url = interaction.user.display_avatar)
        elif (len(user_ids) > 1):
            actor_user = await interaction.client.fetch_user(user_ids[0])
            target_user = await interaction.client.fetch_user(user_ids[1])

            fetched_users.extend([actor_user, target_user])

            embed.set_author(name = f"Friendly battle, {actor_user.name} vs {target_user.name}", icon_url = actor_user.display_avatar)
        else:
            embed.set_author(name = "Monster battle")

        final_turn_display = battle_ctx.turn_number + 1
        streak_text = f" - Streak: {streak}" if (isinstance(streak, int)) else ""
        footer_text = ""

        config = get_config()

        WIN_XP = get_setting("xp_amounts", setting_index = "win")
        TIE_XP = get_setting("xp_amounts", setting_index = "tie")
        LOSS_XP = get_setting("xp_amounts", setting_index = "loss")

        match(end_state):
            case "actor_win":
                if (len(user_ids) > 1):
                    footer_text = f"{fetched_users[0].name} won against {fetched_users[1].name} in {final_turn_display} turns!"
                else:
                    footer_text = f"You won in {battle_ctx.turn_number + 1} turns! +{WIN_XP} XP"
                embed.color = discord.Colour.green()
            case "target_win":
                if (len(user_ids) > 1):
                    footer_text = f"{fetched_users[0].name} lost against {fetched_users[1].name} in {final_turn_display} turns!"
                else:
                    footer_text = f"You lost in {final_turn_display} turns! +{LOSS_XP} XP"
                embed.color = discord.Colour.red()
            case "tie":
                footer_text = f"The battle was too long, it's a tie!"
                embed.color = discord.Colour.light_gray()

                if (len(user_ids) == 1):
                    footer_text += f" +{TIE_XP} XP"
            case "tie_death":
                footer_text = f"Both teams died, it's a tie!"
                embed.color = discord.Colour.light_gray()

                if (len(user_ids) == 1):
                    footer_text += f" +{TIE_XP} XP"

        embed.set_footer(text = f"{footer_text} [{current_turn_number + 1}/{final_turn_display}]{streak_text}")

        for battle_team in [turn_snapshot.actor_team, turn_snapshot.target_team]:
            team_name = battle_team.bt_id
            embed_value = ""

            for battle_monster in battle_team.monsters:
                weapon_string = "No weapon"

                if (battle_monster.weapon is not None):
                    weapon_string = await get_weapon_string(None, None, defined_data = battle_monster.weapon_model)

                monster_config = get_monster_config(m_type = battle_monster.m_type)
                monster_hp = round(battle_monster.get_stat("hp")["current"])
                monster_mana = round(battle_monster.get_stat("mana")["current"])
                monster_lvl = get_level(battle_monster.xp)
                
                effect_emojis = [effect.emoji for effect in battle_monster.effects if current_turn_number >= effect.start_turn]
                stat_emojis = get_emoji("stats")

                effect_string = f"\n> {''.join(effect_emojis)}" if effect_emojis else "\n"

                embed_value += f"""L.{monster_lvl} {monster_config["emoji"]} **{battle_monster.name}** {weapon_string} 
                > {stat_emojis[0]}: **`{monster_hp}`** {stat_emojis[3]}: **`{monster_mana}`**{effect_string}
                """

            embed.add_field(name = f"**{team_name}**", value = f"\n{embed_value}", inline = True)

        return embed
    except Exception as e:
        raise ValueError(f"[ERROR]: While showing battle embed, message: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Battle(bot))
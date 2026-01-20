from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
from utils.util_file import get_user, get_config, get_monster, get_emoji, get_rarity_info, get_monster_config, get_setting, get_cooldown

class Monster(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot 

    monster_command = app_commands.Group(
            name="monster", 
            description="Monster related commands"
    )

    @monster_command.command(
            name = "collection",
            description = "Show collection of owned monsters"
    )
    async def monster_collection(self, interaction:discord.Interaction):
        try:
            # defer the response because we are requesting from the database and the slash command may fail
            await interaction.response.defer()

            cooldown = await get_cooldown(interaction.user.id, interaction.command.root_parent.name, set = True, message = True)

            if (cooldown):
                return await interaction.followup.send(content = cooldown)
            
            user_data = await get_user(interaction.user.id)

            if (not user_data):
                raise ValueError("Missing user in the database!")

            config = get_config()
            user_owned_monsters = await get_monster(interaction.user.id)

            if (not isinstance(user_owned_monsters, list)):
                raise ValueError(f"Expected list got {type(user_owned_monsters)} when requesting user owned monsters!")

            embed = discord.Embed(
                title = f"{get_emoji("card_box")} {get_emoji("monster")} {interaction.user.name}'s Monster collection {get_emoji("monster")} {get_emoji("card_box")}",
                color = discord.Color.dark_blue()
            )

            monsters_in_config = {}

            for monster_data in user_owned_monsters:
                monster_config = get_monster_config(m_type = monster_data.m_type)

                if (monster_config is None):
                    raise ValueError(f"Monster is missing in config!")
                
                # copy seqment data from data to config, so we can work with this later
                monster_config["seq"] = monster_data.seq
                monster_rarity = monster_config["rarity"]

                if monster_rarity not in monsters_in_config:
                    monsters_in_config[monster_rarity] = []

                monsters_in_config[monster_rarity].append(monster_config)

            config_rarities = config["rarities"]

            for rarity, rarity_info in config_rarities.items():
                if (not rarity in monsters_in_config):
                    continue 
                
                rarity_monsters = monsters_in_config[rarity]
                rarity_emoji = rarity_info["emoji"]

                step = get_setting("monsters_in_line")

                for index in range(0, len(rarity_monsters), step):
                    monsters_to_display = rarity_monsters[index : index + step]
                    emojis_of_monsters = [f"{m["emoji"]}{convert_to_index(m["seq"])}" for m in monsters_to_display]

                    string_to_display = " ".join(emojis_of_monsters)

                    if (index ==  0):
                        string_to_display = f"{rarity_emoji} {string_to_display}"
                    else:
                        string_to_display = f"{get_emoji("blank")} {string_to_display}"

                    embed.add_field(name = "", value = string_to_display + "\n", inline = False)

            await interaction.followup.send(embed = embed)
        except Exception as e:
            await interaction.followup.send(f"[ERROR]: While listing monsters, message: {e}")

    @monster_command.command(
            name = "view",
            description = "View monster"
    )
    async def monster_view(self, interaction:discord.Interaction, name:str):
        try:
            # defer the response because we are requesting from the database and the slash command may fail
            await interaction.response.defer()

            cooldown = await get_cooldown(interaction.user.id, interaction.command.root_parent.name, set = True, message = True)

            if (cooldown):
                return await interaction.followup.send(content = cooldown)
            
            user_data = await get_user(interaction.user.id)

            if (not user_data):
                raise ValueError("Missing user in the database!")
            
            monster_data, monster_config = await get_monster(interaction.user.id, name = name)

            if (monster_data is None or monster_config is None):
                raise ValueError("Monster does not exist!")

            embed = discord.Embed(
                title = f"{monster_config['emoji']} {monster_config['name']}",
                color = discord.Color.dark_blue()
            )

            rarity_info = get_rarity_info(monster_config["rarity"])

            def get_stat(name):
                return monster_config["stats"][name]["amount"]

            stat_emojis = get_emoji("stats")
            # TODO: change stat names to emojis

            embed_field = (
                f"**Rarity:** {rarity_info['emoji']} {monster_config['rarity']} \n"
                f"**Amount:** {monster_data.seq}x \n"
                f"**ID:** `{monster_data.m_id}`\n\n"
                f"**Stats:**\n"
                f"**{stat_emojis[0]}: `{get_stat('hp')}` {stat_emojis[1]}: `{get_stat('strength')}` {stat_emojis[2]}: `{get_stat('strength_defense')}`**\n"
                f"**{stat_emojis[3]}: `{get_stat('mana')}` {stat_emojis[4]}: `{get_stat('mag')}` {stat_emojis[5]}: `{get_stat('mag_defense')}`**"
            )
            
            embed.add_field(name = "", value = embed_field, inline = False)
            await interaction.followup.send(embed = embed)
        except Exception as e:
            await interaction.followup.send(f"[ERROR]: While viewing monster, message: {e}")


def convert_to_index(number):
    index_numbers = "⁰¹²³⁴⁵⁶⁷⁸⁹"

    converted = [list(index_numbers)[int(n)] for n in list(str(number))]

    return "".join(converted)

async def setup(bot: commands.Bot):
    await bot.add_cog(Monster(bot))
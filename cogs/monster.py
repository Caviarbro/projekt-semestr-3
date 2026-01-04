from __future__ import annotations
import discord, random
from discord import app_commands
from discord.ext import commands
from utils.util_file import get_user, get_config, get_monster, get_emoji, get_rarity_info, get_monster_config

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

            user = await get_user(interaction.user.id)

            if (user is not None):
                user_owned_monsters = await get_monster(interaction.user.id)

                if (not isinstance(user_owned_monsters, list)):
                    raise ValueError(f"Expected list got {type(user_owned_monsters)} when requesting user owned monsters!")

                config = get_config()

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

                    # TODO: sort from common to uncommon and so on..
                    if monster_rarity not in monsters_in_config:
                        monsters_in_config[monster_rarity] = []

                    monsters_in_config[monster_rarity].append(monster_config)

                for rarity, rarity_monsters in monsters_in_config.items():
                    step = config["settings"]["monsters_in_line"]
                    rarity_emoji = get_rarity_info(rarity)["emoji"]

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
            else:
                raise ValueError("Missing user in database!")
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

            user = await get_user(interaction.user.id)

            if (user is not None):
                monster_data, monster_config = await get_monster(interaction.user.id, name = name)

                if (monster_data is None or monster_config is None):
                    raise ValueError("Monster does not exist!")

                config = get_config()

                embed = discord.Embed(
                    title = f"{monster_config['emoji']} {monster_config['name']}",
                    color = discord.Color.dark_blue()
                )

                rarity_info = get_rarity_info(monster_config["rarity"])

                def get_stat(name):
                    return monster_config["stats"][name]["amount"]

                # TODO: change stat names to emojis
                embed.add_field(name = "", value = f"**Rarity:** {rarity_info['emoji']} {monster_config['rarity']} \n", inline = False)
                embed.add_field(name = "", value = f"**Amount:** {monster_data.seq} \n", inline = False)
                embed.add_field(name = "", value = f"**ID:** `{monster_data.m_id}`", inline = False)
                embed.add_field(name = "", value = "\n", inline = False)
                embed.add_field(name = "", value = f"**HP:** {get_stat('hp')} **STR:** {get_stat('strength')} **STR DEF:** {get_stat('strength_defense')}", inline = False)
                embed.add_field(name = "", value = f"**MN:** {get_stat('mana')} **MAG:** {get_stat('mag')} **MAG DEF:** {get_stat('mag_defense')}", inline = False)
                await interaction.followup.send(embed = embed)
            else:
                raise ValueError("Missing user in database!")
        except Exception as e:
            await interaction.followup.send(f"[ERROR]: While viewing monster, message: {e}")


def convert_to_index(number):
    index_numbers = "⁰¹²³⁴⁵⁶⁷⁸⁹"

    converted = [list(index_numbers)[int(n)] for n in list(str(number))]

    return "".join(converted)

async def setup(bot: commands.Bot):
    await bot.add_cog(Monster(bot))
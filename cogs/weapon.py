from __future__ import annotations
import discord, random, sys, traceback
from discord import app_commands
from discord.ext import commands
from utils.util_file import get_user, get_config, get_weapon, get_emoji, get_monster, equip_weapon, unequip_weapon, get_weapon_string, get_quality_info, to_base36_spaced, to_base36, get_monster_config

class Weapon(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot 

    weapon_command = app_commands.Group(
            name="weapon", 
            description="Weapon related commands"
    )

    @weapon_command.command(
            name = "collection",
            description = "Show collection of owned weapons"
    )
    async def weapon_collection(self, interaction:discord.Interaction):
        try:
            # defer the response because we are requesting from the database and the slash command may fail
            await interaction.response.defer()

            user = await get_user(interaction.user.id)

            if (user is not None):
                user_owned_weapons = await get_weapon(interaction.user.id)
                config = get_config()
                
                pages = []
                MAX_PER_PAGE = config["settings"]["weapons_per_page"]


                for index, weapon in enumerate(user_owned_weapons):
                    current_page = index // MAX_PER_PAGE

                    while len(pages) <= current_page:
                        pages.append([])

                    pages[current_page].append(weapon)

                if (not pages):
                    pages = [[]]

                embed = await show_page(interaction, pages, 0)

                await interaction.followup.send(embed = embed, view = InteractionHandler(pages))
            else:
                raise ValueError("Missing user in database!")
        except Exception as e:
            await interaction.followup.send(f"[ERROR]: While listing weapons, message: {e}")

    @weapon_command.command(
            name = "view",
            description = "View weapon"
    )
    async def weapon_view(self, interaction:discord.Interaction, id:str):
        try:
            # defer the response because we are requesting from the database and the slash command may fail
            await interaction.response.defer()

            user = await get_user(interaction.user.id)

            if (user is not None):
                weapon_data, weapon_config = await get_weapon(interaction.user.id, id)

                if (weapon_data is None or weapon_config is None):
                    raise ValueError("Monster does not exist!")

                config = get_config()

                embed = discord.Embed(
                    title = f"{weapon_config['default_emoji']} {weapon_config["name"]}",
                    color = discord.Color.dark_blue()
                )

                stats = []
                stat_emojis = get_emoji("stats")
                weapon_description : str = weapon_config["desc"]

                # converting qualities from % to actually stat numbers
                for index, quality in enumerate(weapon_data.qualities):
                    stat = weapon_config["stats"][index]
                    value = stat["min"] + (stat["max"] - stat["min"]) * (quality / 100)

                    stats.append(value)

                    weapon_description = weapon_description.replace(f"[{index}]", f"**{quality}**")
                    
                    if ("name" in stat):
                        weapon_description = weapon_description.replace(f"[name({index})]", stat_emojis[stat["name"]])

                passive_descriptions = []

                for passive_data in weapon_data.passives:
                    passive_config = next(
                        (p for p in config["passives"] if p["type"] == passive_data.p_type),
                        None
                    )

                    if (not passive_config):
                        raise ValueError(f"Passive with type {passive_data.p_type} does not exist in config!")
                    
                    _, passive_rarity_info = get_quality_info(passive_data.qualities)

                    passive_description : str = passive_config["desc"]
                    passive_emoji = passive_config["emojis"][passive_rarity_info["type"]]

                    for index, quality in enumerate(passive_data.qualities):
                        stat = passive_config["stats"][index]
                        passive_description = passive_description.replace(f"[{index}]", f"**{quality}**")
                        
                        if ("name" in stat):
                            passive_description = passive_description.replace(f"[name({index})]", stat_emojis[stat["name"]])

                    passive_description = f"{passive_emoji} **{passive_config["name"]}:**\n > {passive_description}\n"
                    passive_descriptions.append(passive_description)

                # TODO: Add effects to the description
                embed.add_field(name = "", value = f"**ID:** **`{to_base36(weapon_data.w_id)}`**", inline = False)
                embed.add_field(name = "", value = f"**Owner:** {interaction.user.name}", inline = False)
                embed.add_field(name = "", value = f"**Mana cost:** {stats[0]} {stat_emojis["mana"]}", inline = False)
                embed.add_field(name = "", value = f"**Description:**\n > {weapon_description}", inline = False)
                embed.add_field(name = "", value = "".join(passive_descriptions), inline = False)

                await interaction.followup.send(embed = embed)
            else:
                raise ValueError("Missing user in database!")
        except Exception as e:
            await interaction.followup.send(f"[ERROR]: While viewing weapon, message: {e}")

    @weapon_command.command(
            name = "equip",
            description = "Equip weapon to monster"
    )

    async def weapon_equip(self, interaction:discord.Interaction, id:str, monster_name:str):
        try:
            # defer the response because we are requesting from the database and the slash command may fail
            await interaction.response.defer()

            user = await get_user(interaction.user.id)

            if (user is not None):
                weapon_string = await get_weapon_string(interaction.user.id, id, "id")
                monster_config = get_monster_config(monster_name = monster_name)

                equipped = await equip_weapon(interaction.user.id, id, monster_name)

                if (equipped):
                    await interaction.followup.send(f"{get_emoji("success")} Successfully equipped {monster_config['emoji']} to {weapon_string}!")
            else:
                raise ValueError("Missing user in database!")
        except Exception as e:
            await interaction.followup.send(f"[ERROR]: While equipping weapon, message: {e}")

    @weapon_command.command(
            name = "unequip",
            description = "Unequip weapon"
    )

    async def weapon_unequip(self, interaction:discord.Interaction, id:str):
        try:
            # defer the response because we are requesting from the database and the slash command may fail
            await interaction.response.defer()

            user = await get_user(interaction.user.id)

            if (user is not None):
                weapon_string = await get_weapon_string(interaction.user.id, id, "id")

                await unequip_weapon(interaction.user.id, id)

                await interaction.followup.send(f"{get_emoji("success")} Successfully unequipped {weapon_string}!")
            else:
                raise ValueError("Missing user in database!")
        except Exception as e:
            await interaction.followup.send(f"[ERROR]: While unequipping weapon, message: {e}")

class InteractionHandler(discord.ui.View):
    def __init__(self, pages):
        super().__init__(timeout=120)
        self.pages = pages
        self.index = 0

    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.secondary)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = (self.index - 1) % len(self.pages)
        await interaction.response.edit_message(
            embed = await show_page(interaction, self.pages, self.index),
            view = self
        )

    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = (self.index + 1) % len(self.pages)
        await interaction.response.edit_message(
            embed = await show_page(interaction, self.pages, self.index),
            view = self
        )


async def show_page(interaction: discord.Interaction, pages, page_number):
    try:
        config = get_config()

        embed = discord.Embed(
            title = f"{get_emoji("card_box")} {get_emoji("weapon")} {interaction.user.name}'s Weapon collection {get_emoji("weapon")} {get_emoji("card_box")}",
            color = discord.Color.dark_blue()
        )

        # no weapon or page exceeded
        if (not pages or page_number >= len(pages) or not pages[page_number]):
            embed.add_field(name = "", value = "No weapons to be displayed!")
            embed.set_footer(text="Page 1/1")
            return embed

        longest_id_length = -1

        # get longest id, so we can space out every other so it looks clean
        for weapon_data in pages[page_number]:
            id_len = len(to_base36(weapon_data.w_id))

            if (id_len > longest_id_length):
                longest_id_length = id_len

        for weapon_data in pages[page_number]:
            # weapon
            weapon_config = next(
                (w for w in config["weapons"] if w["type"] == weapon_data.w_type),
                None
            )

            if (not weapon_config):
                raise ValueError(f"Weapon with type {weapon_data.w_type} does not exist in config!")
            
            weapon_quality, weapon_rarity_info = get_quality_info(weapon_data.qualities)

            short_id = to_base36_spaced(weapon_data.w_id, longest_id_length)
            weapon_emoji = weapon_config["emojis"][weapon_rarity_info["type"]]
            
            # monster
            monster_string = ""

            equipped_monster_id = weapon_data.e_mid

            if (equipped_monster_id != -1):
                _, monster_config = await get_monster(interaction.user.id, id = equipped_monster_id)

                monster_string = f"| {monster_config['emoji']} {monster_config['name']}"

            # passive
            passive_emojis = []

            for passive_data in weapon_data.passives:
                passive_config = next(
                    (p for p in config["passives"] if p["type"] == passive_data.p_type),
                    None
                )

                if (not passive_config):
                    raise ValueError(f"Passive with type {passive_data.p_type} does not exist in config!")
                
                _, passive_rarity_info = get_quality_info(passive_data.qualities)

                passive_emojis.append(passive_config["emojis"][passive_rarity_info["type"]])

            embed.add_field(name = "", value = f"**`{short_id}`** {weapon_rarity_info['emoji']} {weapon_emoji}{''.join(passive_emojis)} **{weapon_config['name']}** {weapon_quality} % {monster_string}\n", inline = False)

        embed.set_footer(text = f"Page: {page_number + 1}/{len(pages)}")
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line = exc_tb.tb_lineno

        print(f"ERROR at {line}")
        raise ValueError(f"[ERROR]: While building embed, message: {e}")
    
    return embed

async def setup(bot: commands.Bot):
    await bot.add_cog(Weapon(bot))
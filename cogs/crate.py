from __future__ import annotations
import discord, random
from discord import app_commands
from discord.ext import commands
from utils.util_file import get_user, get_config, save_weapon, get_quality_info, get_setting, get_cooldown, roll_quality, process_command_cost

class Crate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot 

    @app_commands.command(
            name="crate", 
            description="Open for items"
    )
    async def crate(self, interaction:discord.Interaction, amount:int):
        try:
            # defer the response because we are requesting from the database and the slash command may fail
            await interaction.response.defer()

            cooldown = await get_cooldown(interaction.user.id, interaction.command.name, set = True, message = True)

            if (cooldown):
                return await interaction.followup.send(content = cooldown)

            MAX_CRATES = get_setting("max_crates")
            if (amount > MAX_CRATES):
                amount = MAX_CRATES
                
            # user data check is inside of this function, so it doesn't make sense to call the function here as well
            not_enough_to_process = await process_command_cost(interaction.user.id, interaction.command.name, multiplier = amount)

            if (not_enough_to_process):
                return await interaction.followup.send(content = not_enough_to_process)
            
            generated_items = generate_weapon(amount)

            found_weapons_text = []

            for weapon_item in generated_items:
                [weapon_config, weapon_qualities] = weapon_item[0]
                generated_passives = weapon_item[1]

                weapon_quality, weapon_rarity_info = get_quality_info(weapon_qualities)

                weapon_text = ""
                weapon_emoji = weapon_config["emojis"][weapon_rarity_info["type"]]

                passives_text = ""
                for passive_item in generated_passives:
                    [passive_config, passive_qualities] = passive_item

                    passive_quality, passive_rarity_info = get_quality_info(passive_qualities)
                    passive_emoji = passive_config["emojis"][passive_rarity_info["type"]]

                    passives_text += passive_emoji

                weapon_text = f"{weapon_emoji}{passives_text}"

                found_weapons_text.append(weapon_text)
                await save_weapon(interaction.user.id, weapon_config["type"], weapon_qualities, generated_passives)

            await interaction.followup.send(f"You found following items: {", ".join(found_weapons_text)}!")
                
        except Exception as e:
            await interaction.followup.send(f"[ERROR]: While opening crate, message: {e}")

def generate_weapon(amount):
    config = get_config()

    weapon_list = config["weapons"]
    passive_list = config["passives"]

    new_weapons = []

    for _ in range(0, amount):
        weapon_qualities = []
        new_passives = []

        new_weapon = weapon_list[random.randrange(0, len(weapon_list))]   

        # generate qualities depending on how many stats the weapon has
        for _ in range(len(new_weapon["stats"])):
            weapon_qualities.append(roll_quality())

        for _ in range(new_weapon["passive_count"]):
            new_passive = passive_list[random.randrange(0, len(passive_list))]
            passive_qualities = []

            for _ in range(0, len(new_passive["stats"])):
                passive_qualities.append(roll_quality())

            new_passives.append([new_passive, passive_qualities])

        new_weapons.append([[new_weapon, weapon_qualities], new_passives])

    return new_weapons

async def setup(bot: commands.Bot):
    await bot.add_cog(Crate(bot))
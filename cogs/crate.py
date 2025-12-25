from __future__ import annotations
import discord, random
from discord import app_commands
from discord.ext import commands
from utils.util_file import get_user, get_config, save_weapon

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

            user = await get_user(interaction.user.id)

            if (user is not None):
                generated_items = generate_weapon(amount)

                weapon_emojis = []

                for weapon_item in generated_items:
                    [weapon_config, weapon_qualities] = weapon_item[0]
                    generated_passives = weapon_item[1]

                    # TODO: Change to more scalable approach and use quality emojis
                    weapon_emojis.append(weapon_config["emojis"][0])
                    # print(f"[NEW WEAPON]: weapon_config: {weapon_config}\n, w_qualities: {weapon_qualities}\n, passives: {generated_passives}\n")

                    await save_weapon(interaction.user.id, weapon_config["type"], weapon_qualities, generated_passives)

                await interaction.followup.send(f"You found following items: {", ".join(weapon_emojis)}!")
            else:
                raise ValueError("Missing user in database!")
        except Exception as e:
            await interaction.followup.send(f"[ERROR]: While opening crate, message: {e}")

def generate_weapon(amount):
    config = get_config()

    weapon_List = config["weapons"]
    passive_list = config["passives"]

    new_weapons = []

    for _ in range(0, amount):
        weapon_qualities = []
        new_passives = []

        new_weapon = weapon_List[random.randrange(0, len(weapon_List))]   

        # generate qualities depending on how many stats the weapon has
        for _ in range(0, len(new_weapon["stats"])):
            weapon_qualities.append(random.randrange(0, config["settings"]["max_quality"]))

        for _ in range(0, new_weapon["passive_count"]):
            new_passive = passive_list[random.randrange(0, len(passive_list))]
            passive_qualities = []

            for _ in range(0, len(new_passive["stats"])):
                passive_qualities.append(random.randrange(0, config["settings"]["max_quality"]))

            new_passives.append([new_passive, passive_qualities])

        new_weapons.append([[new_weapon, weapon_qualities], new_passives])

    return new_weapons

async def setup(bot: commands.Bot):
    await bot.add_cog(Crate(bot))
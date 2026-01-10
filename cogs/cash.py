from __future__ import annotations
import discord, random, sys, traceback
from discord import app_commands
from discord.ext import commands
from utils.util_file import get_user, get_config, get_cooldown, get_setting, get_cash, update_cash, get_weapon, get_quality_info, get_db, get_monster, get_rarity_info

class Cash(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot 

    @app_commands.command(
            name="cash", 
            description="See your $ balance"
    )
    async def cash(self, interaction:discord.Interaction):
        try:
            # defer the response because we are requesting from the database and the slash command may fail
            await interaction.response.defer()

            cooldown = await get_cooldown(interaction.user.id, interaction.command.name, set = True, message = True)

            if (cooldown):
                return await interaction.followup.send(content = cooldown)
            
            # user data check is inside of this function, so it doesn't make sense to call the function here as well
            user_cash = await get_cash(interaction.user.id)

            await interaction.followup.send(f"Your current balance is: **{user_cash}$**!")
        except Exception as e:
            await interaction.followup.send(f"[ERROR]: While using cash, message: {e}") 

    @app_commands.command(
            name="pay", 
            description="Pay cash to another user!"
    )
    async def pay(self, interaction:discord.Interaction, user:discord.User, amount:int):
        try:
            # defer the response because we are requesting from the database and the slash command may fail
            await interaction.response.defer()

            cooldown = await get_cooldown(interaction.user.id, interaction.command.name, set = True, message = True)

            if (cooldown):
                return await interaction.followup.send(content = cooldown)
            
            if (amount < 0):
                return await interaction.followup.send(content = "You can't send negative amount of $!")
            
            # user data check is inside of this function, so it doesn't make sense to call the function here as well
            user_cash = await get_cash(interaction.user.id)

            if (amount > user_cash):
                return await interaction.followup.send(content = "You don't have enough $!")
            
            await update_cash(interaction.user.id, -amount)
            await update_cash(user.id, amount)

            await interaction.followup.send(f"<@{interaction.user.id} sent **{amount}$** to <@{user.id}>!")
        except Exception as e:
            await interaction.followup.send(f"[ERROR]: While paying cash, message: {e}")

    @app_commands.command(
            name="sell", 
            description="Sell your monster/weapon"
    )
    async def sell(self, interaction:discord.Interaction, monster_name:str = None, weapon_id:str = None):
        try:
            # defer the response because we are requesting from the database and the slash command may fail
            await interaction.response.defer()

            cooldown = await get_cooldown(interaction.user.id, interaction.command.name, set = True, message = True)

            if (cooldown):
                return await interaction.followup.send(content = cooldown)
            
            if (not monster_name and not weapon_id):
                raise ValueError("You need to pick at least one - monster_name/weapon_id")
            db = get_db()

            sell_profit = 0
            sell_string = ""

            if (monster_name):
                monster_data, monster_config = await get_monster(interaction.user.id, name = monster_name)
                rarity_info = get_rarity_info(monster_config["rarity"])

                cost = rarity_info["sell"]["monster"]
                sell_profit += cost
                
                await db.users.update_one(
                    {"u_id": interaction.user.id, "monsters.m_type": monster_config["type"]},
                    {"$inc": {"monsters.$.seq": -1}}
                )

                sell_string += f"monster **{monster_config["name"]}**, "

                await update_cash(interaction.user.id, cost)

            if (weapon_id):
                weapon_data, weapon_config = await get_weapon(interaction.user.id, weapon_id)
                weapon_quality, weapon_rarity_info = get_quality_info(weapon_data.qualities)

                cost = weapon_rarity_info["sell"]["weapon"]
                sell_profit += cost

                await db.users.update_one(
                    {"u_id": interaction.user.id},
                    {"$pull": {"weapons": {"w_id": weapon_data.w_id}}}
                )

                sell_string += f"weapon **`{weapon_id.upper()}`**, "

                await update_cash(interaction.user.id, cost)

            sell_string = f"You sold {sell_string} for **{sell_profit}$**!"
            await interaction.followup.send(content = sell_string)
        except Exception as e:
            await interaction.followup.send(f"[ERROR]: While selling, message: {e}")
async def setup(bot: commands.Bot):
    await bot.add_cog(Cash(bot))
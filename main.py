import discord, logging, os
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from os.path import dirname, join, realpath
from motor.motor_asyncio import AsyncIOMotorClient
from utils.database import get_db, get_client

# Loading token variable
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Logging bot activity
CURRENT_DIR = dirname(realpath(__file__))
FILE_DIR = join(CURRENT_DIR, "discord.log")

handler = logging.FileHandler(filename= FILE_DIR, encoding="utf-8", mode="w")

# Intents for bot to have access directly to messages and members
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix = commands.when_mentioned_or("m"), intents = intents)
        
    async def setup_hook(self):
        COGS_DIR = join(CURRENT_DIR, "cogs")

        self.mongo_client = get_client()
        self.db = get_db()
        
        for filename in os.listdir(COGS_DIR):
            if (filename.endswith(".py") and filename != "__init__.py"):
                await self.load_extension(f"cogs.{filename[:-3]}")
        
        try:
            await self.tree.sync()

            # logging.info("Synced commands globally!")
        except:
            print("[BOT]: Error while syncing commands!")
            # logging.info("[ERROR]: While syncing commands!")

    async def on_ready(self):
        print(f"[BOT]: {self.user.name} is ready to be deployed!")

    async def on_member_join(self, member):
        await member.send(f"Welcome to the server {member.name}!")
        
if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("Set DISCORD_TOKEN in .env file!")

    bot = Bot()
    bot.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)
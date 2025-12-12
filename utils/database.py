import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load enviroment variables
load_dotenv()

# Load database
MONGO_URI = os.getenv('DATABASE_URL')

mongo_client = AsyncIOMotorClient(MONGO_URI)
mongo_db = mongo_client["monsterbase"]

def get_db():
    return mongo_db

def get_client():
    return mongo_client
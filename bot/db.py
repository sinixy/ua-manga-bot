import motor.motor_asyncio
from bot.config import Config
from asyncio import sleep


client = motor.motor_asyncio.AsyncIOMotorClient(Config.DB_HOST)
db = client[Config.DB_NAME]
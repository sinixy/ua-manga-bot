from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler_di import ContextSchedulerDecorator

from bot.config import Config


scheduler = ContextSchedulerDecorator(
    AsyncIOScheduler(
        jobstores={"default": MongoDBJobStore(host=Config.DB_HOST)}
    )
)
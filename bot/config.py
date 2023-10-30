from datetime import timedelta
import os



class Config:
    BOT_TOKEN: str = os.environ['BOT_TOKEN']
    
    DB_HOST: str = os.environ['DB_HOST']
    DB_NAME: str = os.environ['DB_NAME']

    MINOR_REMINDER_INTERVAL = timedelta(days=3*30)
    MAJOR_REMINDER_INTERVAL = timedelta(days=6*30)
    CONFIRM_REMINDER_INTERVAL = timedelta(days=14)
    # MINOR_REMINDER_INTERVAL = timedelta(seconds=10)
    # MAJOR_REMINDER_INTERVAL = timedelta(seconds=30)
    # CONFIRM_REMINDER_INTERVAL = timedelta(seconds=2)

    ITEMS_PER_PAGE = 20
    MAX_TEAM_NAME_LENGTH = 50
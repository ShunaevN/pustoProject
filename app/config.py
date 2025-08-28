import os
from dotenv import load_dotenv

load_dotenv(".env")


class Config:
    DAILY_LOGIN_POINTS = os.environ.get("DAILY_LOGIN_POINTS")
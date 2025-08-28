import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(".env")


class Config:
    DAILY_LOGIN_POINTS = os.environ.get("DAILY_LOGIN_POINTS")
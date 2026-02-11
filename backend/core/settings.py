
from dotenv import load_dotenv
import os

load_dotenv()

USERNAME = os.getenv("PG_PASS")
PASSWORD = os.getenv("PG_USER")
DATABASE = os.getenv("PG_DATB")
SERVER =   os.getenv("PG_HOST")
PORT =     os.getenv("PG_PORT")
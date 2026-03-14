from dotenv import load_dotenv
import os

load_dotenv()

PG_USER = os.getenv("PG_USER")
PG_PASS = os.getenv("PG_PASS")
PG_DB = os.getenv("PG_DB")
PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")


DATABASE_URL = (
    f"postgresql+psycopg2://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_DB}"
)

print("DATABASE_URL",DATABASE_URL)
print("#"*100)

class Settings:
    DATABASE_URL = DATABASE_URL

settings = Settings()
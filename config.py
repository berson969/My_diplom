import os


PG_USER = os.getenv("PG_USER", "some_user")
PG_PASSWORD = os.getenv("PG_PASSWORD", "secret")
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", 5432))
PG_DB = os.getenv("PG_DB", "diplom_db")

PG_DSN = os.getenv("PG_DSN", f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}")
SECRET_KEY = os.getenv("SECRET_KEY", "fjk3ghg1hr3ke@kfl3j3afk23485968456bj3vbj5460mv")
DEBUG = os.getenv("DEBUG", True)
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "127.0.0.1, ")

CELERY_BROKER = f"redis://{PG_HOST}:6379/1"
CELERY_BACKEND = f"redis://{PG_HOST}:6379/2"

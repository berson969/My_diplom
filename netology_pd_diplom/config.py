import os
import environ

env = environ.Env(DEBUG=(bool, True))
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

PG_USER = os.getenv("PG_USER", "some_user")
PG_PASSWORD = os.getenv("PG_PASSWORD", "secret")
PG_HOST = os.getenv("PG_HOST", "db")
PG_PORT = int(os.getenv("PG_PORT", 5432))
PG_DB = os.getenv("PG_DB", "diplom_db")

PG_DSN = os.getenv("PG_DSN", f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}")
SECRET_KEY = os.getenv("SECRET_KEY", "fjk3ghg1hr3ke@kfl3j3afk23485968456bj3vbj5460mv")
DEBUG = os.getenv("DEBUG", True)
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "127.0.0.1, ")

EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.mail.ru')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'netology-pdiplom@mail.ru')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'i~8W4rdRPFlo')
EMAIL_PORT = os.getenv('EMAIL_PORT', '465')
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'True')

# REDIS_URL = "redis://localhost:6379"
REDIS_URL = "redis://redis:6379"

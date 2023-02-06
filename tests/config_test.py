import os
import environ

env = environ.Env(DEBUG=(bool, True))
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

EMAIL_USER = os.getenv('EMAIL_USER', 'root_user1@admin.ru')
PASSWORD_USER1 = os.getenv('USER_PASSWORD1', 'qw12ertyuiop12')
PASSWORD_USER2 = os.getenv('USER_PASSWORD2', 'qw12ertyuiop12')
FIRST_NAME = os.getenv('FIRST_NAME', 'first')
LAST_NAME = os.getenv('LAST_NAME', 'last')
SUR_NAME = os.getenv('SUR_NAME', 'surname')
COMPANY = os.getenv('COMPANY', 'netology')
POSITION = os.getenv('POSITION', 'student')

CITY = os.getenv('CITY', 'Vladivostok')
STREET = os.getenv('STREET', 'Shoshina')
HOUSE = os.getenv('HOUSE', '17A')
STRUCTURE = os.getenv('STRUCTURE', 'AA')
BUILDING = os.getenv('BUILDING', '1')
APARTMENT = os.getenv('APARTMENT', '196')
PHONE = os.getenv('PHONE', '+7 (423) 279-05-64')

URL = os.getenv('URL', 'https://raw.githubusercontent.com/berson969/My_diplom/main/data/shop2.yaml')


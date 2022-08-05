from os import environ
from dotenv import load_dotenv
load_dotenv('.env')

APP_DEBUG = environ.get('APP_DEBUG')

SECRET_KEY = environ.get('APP_SECRET')

MAIL_USERNAME = environ.get("MAIL_USERNAME")


S3_BUCKET = environ.get("S3_BUCKET")
S3_KEY = environ.get("S3_KEY")
S3_SECRET = environ.get("S3_SECRET")
S3_LOCATION = environ.get("S3_LOCATION")


# config MySQL
MYSQL_HOST = environ.get("MYSQL_HOST")
MYSQL_USER = environ.get("MYSQL_USER")
MYSQL_PASSWORD = environ.get("MYSQL_PASSWORD")
MYSQL_DB = environ.get("MYSQL_DB")
MYSQL_CURSORCLASS = environ.get("MYSQL_CURSORCLASS")

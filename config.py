from os import environ
from dotenv import load_dotenv
load_dotenv('.env')

APP_DEBUG = environ.get('APP_DEBUG')

SECRET_KEY =  environ.get('APP_SECRET')

MAIL_SERVER =  environ.get("MAIL_SERVER")
MAIL_PORT =  environ.get("MAIL_PORT")
MAIL_USE_TLS =  environ.get("MAIL_USE_TLS")
MAIL_USE_SSL =  environ.get("MAIL_USE_SSL")
MAIL_USERNAME =  environ.get("MAIL_USERNAME")
MAIL_PASSWORD =  environ.get("MAIL_PASSWORD")


S3_BUCKET  =  environ.get("S3_BUCKET")
S3_KEY =  environ.get("S3_KEY")
S3_SECRET =  environ.get("S3_SECRET")
S3_LOCATION =  environ.get("S3_LOCATION")
# app.config['S3_ENDPOINT'] = 'http://localhost:9000'


#config MySQL
MYSQL_HOST =  environ.get("MYSQL_HOST")
MYSQL_USER =  environ.get("MYSQL_USER")
MYSQL_PASSWORD =  environ.get("MYSQL_PASSWORD")
MYSQL_DB =  environ.get("MYSQL_DB")
MYSQL_CURSORCLASS =  environ.get("MYSQL_CURSORCLASS")
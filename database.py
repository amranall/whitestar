# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.ext.declarative import declarative_base

# URL_DATABASE = 'sqlite:///whitestar.db'

# engine = create_engine(URL_DATABASE, connect_args={'check_same_thread': False})
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = declarative_base()

# #  connecting to db using pymysql
# import pymysql
# from config import settings

# def get_db():
#     connection = pymysql.connect(
#         host=settings.db_host,
#         user=settings.db_user,
#         password=settings.db_password,
#         database=settings.db_name,
#         port=settings.db_port
#     )

#     return connection


# Connecting using sqlalchemy
# Path: community_service_backend/app/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings
import pymysql

# >>>> removing the logging as I fixed this issue
# # adding logging of sqlalchemy commands
# import logging
# # Configure logging
# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Connection string for PyMySQL
SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{settings.db_user}:{settings.db_password}@"
    f"{settings.db_host}:{settings.db_port}/{settings.db_name}"
)

# Create the SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create a session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency to get a session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

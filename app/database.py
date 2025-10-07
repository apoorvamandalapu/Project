from sqlalchemy import create_engine #connection to db
from sqlalchemy.orm import sessionmaker #creates session for interacting
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base() #creates base class for models

DATABASE_URL = "sqlite:///./races.db"

engine = create_engine(DATABASE_URL, connect_args = {"check_same_thread":False}) #use connections across multiple threads
SessionLocal = sessionmaker(autocommit=False, autoflush=False,bind=engine) #not auto committed/pushed



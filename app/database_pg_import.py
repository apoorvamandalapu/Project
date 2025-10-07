from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

ImportBase = declarative_base()

POSTGRES_IMPORT_URL = "postgresql+psycopg2://dbuser:postgres@localhost:5432/drivers_constructors"

import_engine = create_engine(POSTGRES_IMPORT_URL)
ImportPGSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=import_engine)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

PgBase = declarative_base()

POSTGRES_URL = "postgresql+psycopg2://f1user:postgres@localhost:5432/drivers"

pg_engine = create_engine(POSTGRES_URL)
PGSessionLocal = sessionmaker(autocommit=False, autoflush = False, bind = pg_engine)


from sqlalchemy import Column, String, Integer, Date
from app.database import Base
from app.database_pg import PgBase

#defines DB (how fastapi stores/fetches from DB)
class RaceDB(Base):
    __tablename__ = "races"
    id = Column(Integer, primary_key=True, index=True)
    season = Column(String, index=True)
    round = Column(String)
    raceName = Column(String)
    date = Column(String)
    time = Column(String)
    circuit_name = Column(String)
    country = Column(String)

class DriverDB(PgBase):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key = True, index = True)
    driverId = Column(String, unique=True, index=True)
    givenName = Column(String)
    familyName = Column(String)
    code = Column(String, nullable=True)
    nationality = Column(String)
    dateOfBirth = Column(String)
    


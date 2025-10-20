from sqlalchemy import Column, String, Date, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database_pg_import import ImportBase

class Constructors_All(ImportBase):
    __tablename__ = "constructors"
    id = Column(Integer, primary_key=True, index=True)
    season = Column(String, index=True)
    constructorId = Column(String, index=True)
    name = Column(String)
    nationality = Column(String)

    #drivers = relationship("Drivers_All",back_populates="constructors_rel")

class Drivers_All(ImportBase):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True, index=True)
    season = Column(String, index=True)
    permanentNumber = Column(String, index=True)
    givenName = Column(String)
    familyName = Column(String)
    code = Column(String, nullable=True)
    nationality = Column(String)
    constructorId = Column(String, nullable=True)

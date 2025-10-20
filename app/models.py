from pydantic import BaseModel, Field 
from typing import Optional

#defines input/output(of how fastapi talks JSON)
class Driver(BaseModel):
    driverId: str
    permanentNumber: Optional[str] = None
    code: Optional[str] = None
    url: Optional[str] = None
    givenName: str
    familyName: str
    dateOfBirth: Optional[str] = None  
    nationality: str

class LocationName(BaseModel):
    lat: Optional[str] = None
    long: Optional[str] = None
    locality: Optional[str] = None
    country: str


class CircuitName(BaseModel):
    circuitId: str
    url: Optional[str] = None
    circuitName: Optional[str] = None
    Location: Optional[LocationName] = None


class RaceEvent(BaseModel):
    date: Optional[str] = None
    time: Optional[str] = None


class Race(BaseModel):
    season: str
    round: Optional[str] = None
    url: Optional[str] = None
    raceName: Optional[str] = None
    Circuit: Optional[CircuitName] = None
    date: str
    time: Optional[str] = None
    FirstPractice: Optional[RaceEvent] = None
    SecondPractice: Optional[RaceEvent] = None
    ThirdPractice: Optional[RaceEvent] = None
    Sprint: Optional[RaceEvent] = None
    SprintQualifying: Optional[RaceEvent] = None
    Qualifying: Optional[RaceEvent] = None

class Constructor(BaseModel):
    constructorId: str
    url: str = Field(None)
    name: str
    nationality: str

class RaceCreate(BaseModel):
    season: str
    round: Optional[str] = None
    raceName: Optional[str] = None
    date: str
    time: Optional[str] = None
    circuit_name: Optional[str] = None
    country: Optional[str] = None

class DriverCreate(BaseModel):
    driverId: str
    givenName: str
    familyName: str
    code: Optional[str] = None
    nationality: Optional[str] = None
    dateOfBirth: Optional[str] = None

class AgentQuery(BaseModel):
    query: str

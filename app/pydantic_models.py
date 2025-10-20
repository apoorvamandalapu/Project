from pydantic import BaseModel
from typing import List,Optional, Dict

class DriverDBModel(BaseModel):
    driverId: str
    permanentNumber: Optional[str] = None
    code: Optional[str] = None
    givenName: str
    familyName: str
    nationality: str

class DriversInfo(BaseModel):
    givenName: str
    familyName: str
    nationality: str

class DriverQuery(BaseModel):
    name: str
    season: str

class DriverResult(BaseModel):
    drivers: List[DriverDBModel]

class APIQuery(BaseModel):
    query: str

class APIResult(BaseModel):
    endpoint: str
    status: str
    answer: Dict
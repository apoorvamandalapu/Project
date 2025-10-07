from fastapi import FastAPI, Request,Query, HTTPException, Depends
import requests
from typing import List, Dict
from difflib import SequenceMatcher
from app.models import Driver, Race, Constructor, RaceCreate, DriverCreate, AgentQuery

from sqlalchemy.orm import Session
from app.database import SessionLocal, Base, engine
from app.db_models import RaceDB

from app.database_pg import pg_engine, PGSessionLocal, PgBase
from app.db_models import DriverDB

from app.database_pg_import import import_engine, ImportPGSessionLocal, ImportBase
from app.db_models_link_pg import Constructors_All, Drivers_All

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.events import Event

from app.agents.sub_agents.api_agent.agent import api_agent



from app.agents.sub_agents.db_agent.agent import db_agent


Base.metadata.create_all(bind=engine) #creates table if not already present
PgBase.metadata.create_all(bind=pg_engine)
ImportBase.metadata.create_all(bind=import_engine)

app = FastAPI()

BASE_URL = "https://api.jolpi.ca/ergast/f1"



@app.get("/")
def root():
    return {"Message: Welcome to F1 API App!"}

#fetch from API

@app.get("/drivers/{year}",response_model = List[Driver])
def get_drivers(year: int):
    url = f"{BASE_URL}/{year}/drivers.json"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    drivers = data["MRData"]["DriverTable"]["Drivers"]
    return drivers

def fuzzy_match(a:str,b:str, threshold:float=0.7) -> bool:
    ratio = SequenceMatcher(None, a.lower(),b.lower()).ratio()
    return ratio>=threshold

@app.get("/drivers/{year}/filter",response_model = List[Driver])
def filter_drivers(year:int, request: Request,search: str = Query("",description="Search Term"), 
                threshold:float=Query(0.7, ge=0.0, le=1.0),
                limit:int=Query(20,ge=1), offset: int=Query(0,ge=0),sort_by:str = 
                Query("familyName"),sort_order: str = Query("asc")) -> List[Dict]:
    """
    Query() cannot directly parse python dict, Dict[str,str] so we used Request
    """
    #filters = dict(request.query_params)
    filters = {k: v for k, v in request.query_params.items()
        if k not in ["search", "threshold", "limit", "offset", "sort_by", "sort_order"]}
        #because drivers dict dont have values so when used in link it breaks

    url = f"{BASE_URL}/{year}/drivers.json"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    drivers = data["MRData"]["DriverTable"]["Drivers"]

    for field, value in filters.items():
        drivers = [d for d in drivers if field in d and fuzzy_match(str(d[field]),value,threshold)]

    if search:
        search_fields = ["givenName","familyName","code"]
        drivers = [d for d in drivers if any(fuzzy_match(str(d.get(f,"")),search,threshold) for f in search_fields)]
    
    drivers.sort(key = lambda x: x.get(sort_by,""),reverse = (sort_order.lower()=="desc"))
    drivers = drivers[offset:offset+limit]
    return drivers

@app.get("/races/{year}", response_model=List[Race])
def get_races(year: int):
    url = f"{BASE_URL}/{year}/races.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail = f"Failed to fetch races: {e}")
    data = response.json()
    races = data.get("MRData",{}).get("RaceTable",{}).get("Races",[])
    return races

@app.get("/constructors/{year}",response_model=List[Constructor])
def get_constructors(year: int):
    url = f"{BASE_URL}/{year}/constructors.json"
    try: 
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=503,detail=f"Constructor detail not found: {e}")
    data = response.json()
    constructors = data["MRData"]["ConstructorTable"]["Constructors"]
    return constructors

#local db
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#created from API
@app.post("/races/{year}/store")
def store_races(year: int, db: Session = Depends(get_db)):
    url = f"{BASE_URL}/{year}/races.json"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    races = data["MRData"]["RaceTable"]["Races"]

    for r in races:
        race = RaceDB(
            season = r["season"],round = r["round"],raceName = r["raceName"],
            date = r["date"],time = r.get("time"),circuit_name = r["Circuit"]["circuitName"],
            country = r["Circuit"]["Location"]["country"]
        )
        db.add(race)
    db.commit()
    return {"status":"success","races_added":len(races)}

@app.get("/races/local/{year}",response_model = List[RaceCreate])
def get_local_races(year: int, db: Session = Depends(get_db)):
    races = db.query(RaceDB).filter(RaceDB.season == str(year)).all()
    return races

#manual
@app.post("/races/manual",response_model = RaceCreate)
def create_race_manual(race: RaceCreate, db: Session = Depends(get_db)):
    db_race = RaceDB(**race.model_dump()) #converts pydantic model to dict
    db.add(db_race)
    db.commit()
    db.refresh(db_race)
    return db_race

@app.get("/races/manual/{race_id}",response_model = RaceCreate)
def get_race_manual(race_id: int, db: Session = Depends(get_db)):
    db_race = db.query(RaceDB).filter(RaceDB.id == race_id).first()
    if not db_race:
        raise HTTPException(status_code = 404, detail = "Race not found")
    return db_race

@app.put("/races/manual/{race_id}",response_model = RaceCreate)
def update_race_manual(race_id: int, race: RaceCreate, db: Session = Depends(get_db)):
    db_race = db.query(RaceDB).filter(RaceDB.id == race_id).first()
    if not db_race:
        raise HTTPException(status_code=404, detail = "Race not found")
    for key, value in race.model_dump().items():
        setattr(db_race,key,value)
    db.commit()
    db.refresh(db_race)
    return db_race

@app.delete("/races/manual/{race_id}")
def delete_race_manual(race_id: int, db: Session = Depends(get_db)):
    db_race = db.query(RaceDB).filter(RaceDB.id == race_id).first()
    if not db_race:
        raise HTTPException(status_code = 404, detail = "Race not found")
    db.delete(db_race)
    db.commit()
    return {"status":"Success","delete_id":race_id}


#postgres db
def get_pg_db():
    pg_db = PGSessionLocal()
    try:
        yield pg_db
    finally:
        pg_db.close()

@app.post("/drivers/manual",response_model = DriverCreate)
def create_driver(driver: DriverCreate, pg_db: Session = Depends(get_pg_db)):
    db_driver = DriverDB(**driver.model_dump())
    pg_db.add(db_driver)
    pg_db.commit()
    pg_db.refresh(db_driver)
    return db_driver

@app.get("/drivers/manual/{driver_id}",response_model = DriverCreate)
def get_driver(driver_id: int, pg_db: Session = Depends(get_pg_db)):
    db_driver = pg_db.query(DriverDB).filter(DriverDB.id == driver_id).first()
    if not db_driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return db_driver

@app.put("/drivers/manual/{driver_id}",response_model = DriverCreate)
def update_driver(driver_id: int, driver: DriverCreate, pg_db: Session = Depends(get_pg_db)):
    db_driver = pg_db.query(DriverDB).filter(DriverDB.id == driver_id).first()
    if not db_driver:
        raise HTTPException(status_code = 404, detail = "Driver not found")
    for key,value in driver.model_dump().items():
        setattr(db_driver, key, value)
    pg_db.commit()
    pg_db.refresh(db_driver)
    return db_driver

@app.delete("/drivers/manual/{driver_id}")
def delete_driver(driver_id:int, pg_db: Session = Depends(get_pg_db)):
    db_driver = pg_db.query(DriverDB).filter(DriverDB.id == driver_id).first()
    if not db_driver:
        raise HTTPException(status_code = 404, detail = "Driver not found")
    pg_db.delete(db_driver)
    pg_db.commit()
    return {"status": "Success", "deleted_id": driver_id}


#postgres - data stored from api to db
def get_import_db():
    import_db = ImportPGSessionLocal()
    try:
        yield import_db
    finally:
        import_db.close()

@app.post("/constructors/import/{year}")
def import_constructors(year: int, import_db: Session = Depends(get_import_db)):
    url = f"{BASE_URL}/{year}/constructors.json"
    response = requests.get(url)
    response.raise_for_status()
    constructors = response.json()["MRData"]["ConstructorTable"]["Constructors"]
    
    count = 0
    for c in constructors:
        existing = import_db.query(Constructors_All).filter(Constructors_All.season == str(year),
        Constructors_All.constructorId == c["constructorId"]).first()
        if existing:
            continue

        db_constructor = Constructors_All(season= str(year), constructorId=c["constructorId"], name = c["name"],
                                          nationality = c["nationality"])
        import_db.add(db_constructor)
        count+=1
    import_db.commit()
    return {"status": "success", "constructors_added": count}

@app.post("/drivers/import/{year}")
def import_drivers(year: int, import_db: Session = Depends(get_import_db)):
    url = f"{BASE_URL}/{year}/drivers.json"
    response = requests.get(url)
    response.raise_for_status()
    drivers = response.json()["MRData"]["DriverTable"]["Drivers"]

    count = 0
    for d in drivers:
        existing = import_db.query(Drivers_All).filter(Drivers_All.season==str(year),
        Drivers_All.permanentNumber == d["permanentNumber"]).first()
        if existing:
            continue
        db_driver = Drivers_All(season = str(year), permanentNumber=d["permanentNumber"], givenName = d["givenName"],
        familyName = d["familyName"], code = d["code"], nationality = d["nationality"])
        import_db.add(db_driver)
        count+=1
    import_db.commit()
    return {"status": "success", "drivers_added": count}

@app.post("/drivers/link_constructors/{year}")
def link_constructor(year: int, import_db: Session = Depends(get_import_db)):
    url = f"{BASE_URL}/{year}/driverStandings.json"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    standings_lists = data.get("MRData", {}).get("StandingsTable", {}).get("StandingsLists", [])
    
    if not standings_lists:
        return {"status": "failed", "message": "No driver standings found for this year."}

    updated = 0
    for standings in standings_lists:
        driver_standings = standings.get("DriverStandings", [])
        for s in driver_standings:
            driver_info = s.get("Driver",{})
            constructor_info = s.get("Constructors",[])
        
            if not driver_info or not constructor_info:
                continue
        
            driver_permanent_number = driver_info.get("permanentNumber")
            constructorId = constructor_info[0].get("constructorId")

            if not driver_permanent_number or not constructorId:
                continue

            driver = import_db.query(Drivers_All).filter(Drivers_All.season == str(year),
            Drivers_All.permanentNumber == driver_permanent_number).first()

            if driver:
                driver.constructorId = constructorId
                updated+=1

    import_db.commit()
    return {"status": "success", "drivers_linked": updated}

@app.post("/ask_agent")
async def ask_agent(payload: AgentQuery):
    user_input = payload.query
    
    runner = Runner(
        agent=api_agent,
        app_name="f1-ergast-agent",
        session_service=InMemorySessionService()
    )

    event_data = {
        "author": "user",
        "content": {
            "role": "user",
            "parts": [
                {"text": user_input}
            ]
        }
    }
    event = Event(**event_data)

    response = await runner.run(event)
    agent_text = response.output_text if hasattr(response, "output_text") else str(response)

    return {"response": agent_text}

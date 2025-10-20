import json
from typing import Optional, List
import httpx
from pydantic_ai import Agent, RunContext
from sqlalchemy import or_

from app.pydantic_models import DriverQuery, DriverResult, DriverDBModel, APIResult
from app.db_models_link_pg import Drivers_All
from app.database_pg_import import ImportPGSessionLocal

from dotenv import load_dotenv
load_dotenv()

driver_agent = Agent(
    model="gemini-2.5-flash",
    deps_type=DriverQuery,
    system_prompt=(
        "You are a data retrieval agent for Formula 1 driver data.\n"
        "You have access to a tool called `get_drivers(name, season)`.\n"
        "You MUST call this tool to fetch data and return it as JSON.\n"
        "Do not respond in natural language. Only return structured results.\n"
        "If no drivers match, return an empty list."
    )
)

@driver_agent.tool
async def get_drivers(ctx: RunContext, name: Optional[str] = None, season: Optional[str] = None) -> List[DriverDBModel]:
    with ImportPGSessionLocal() as session:
        query = session.query(Drivers_All)
        filters = []
        if name:
            filters.append(
                or_(
                    Drivers_All.givenName.ilike(f"%{name}%"),
                    Drivers_All.familyName.ilike(f"%{name}%")
                )
            )
        if season:
            filters.append(Drivers_All.season == str(season))
        if filters:
            query = query.filter(*filters)
        rows = query.all()
        return [
            DriverDBModel(
                driverId=str(d.id),
                permanentNumber=d.permanentNumber,
                code=d.code,
                givenName=d.givenName,
                familyName=d.familyName,
                nationality=d.nationality
            )
            for d in rows
        ]

async def query_driver_data(query: DriverQuery) -> DriverResult:
    try:
        result = await driver_agent.run(
            f"Find drivers with name='{query.name}' and season='{query.season}'.",
            deps=query
        )
    except Exception as e:
        drivers_list = await get_drivers(None, query.name, query.season)
        return DriverResult(drivers=drivers_list)
    drivers_list: List[DriverDBModel] = []
    if isinstance(result.output, str):
        try:
            data = json.loads(result.output)
            for item in data.get("get_drivers_response", []):
                if isinstance(item, str):
                    item_dict = json.loads(item)
                    drivers_list.append(DriverDBModel(**item_dict))
                elif isinstance(item, dict):
                    drivers_list.append(DriverDBModel(**item))
        except json.JSONDecodeError:
            drivers_list = await get_drivers(None, query.name, query.season)
    elif isinstance(result.output, list):
        drivers_list = result.output
    else:
        drivers_list = await get_drivers(None, query.name, query.season)
    return DriverResult(drivers=drivers_list)

ERGAST_ENDPOINTS = {
    "season": "https://api.jolpi.ca/ergast/f1/seasons/",
    "circuit": "https://api.jolpi.ca/ergast/f1/circuits/",
    "race": "https://api.jolpi.ca/ergast/f1/2025/races/",
    "constructor": "https://api.jolpi.ca/ergast/f1/2025/constructors/",
    "driver": "https://api.jolpi.ca/ergast/f1/2025/drivers/",
    "result": "https://api.jolpi.ca/ergast/f1/2025/results/",
    "sprint": "https://api.jolpi.ca/ergast/f1/2025/sprint/",
    "qualifying": "https://api.jolpi.ca/ergast/f1/2025/qualifying/",
    "pitstop": "https://api.jolpi.ca/ergast/f1/2025/1/pitstops/",
    "lap": "https://api.jolpi.ca/ergast/f1/2025/1/laps/",
    "driverstanding": "https://api.jolpi.ca/ergast/f1/2025/driverstandings/",
    "constructorstanding": "https://api.jolpi.ca/ergast/f1/2025/constructorstandings/",
    "status": "https://api.jolpi.ca/ergast/f1/status/"
}


api_agent = Agent(
    model="gemini-2.5-flash",
    deps_type=str,
    system_prompt=(
        "You are an F1 data agent using Ergast API.\n"
        "You will receive a user question.\n"
        "Decide which API endpoint (season, circuit, race, constructor, driver, result, sprint, qualifying, pitstop, lap, driverstanding, constructorstanding, status) best answers the query.\n"
        "Respond ONLY in JSON format: {\"endpoint\": <endpoint>, \"status\": \"success\" or \"fail\", \"answer\": <data>}.\n"
        "If the query cannot be answered or is invalid, respond politely with status 'fail' and explain in 'answer'."
    )
)

@api_agent.tool
async def fetch_endpoint_data(ctx: RunContext, endpoint: Optional[str] = None) -> dict:
    if not endpoint or endpoint not in ERGAST_ENDPOINTS:
        return {"endpoint": endpoint, "status": "fail", "answer": "Invalid endpoint."}
    
    url = ERGAST_ENDPOINTS[endpoint]
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, timeout=10, follow_redirects=True)
            resp.raise_for_status()
            data = resp.json()
            return {"endpoint": endpoint, "status": "success", "answer": data}
        except Exception as e:
            return {"endpoint": endpoint, "status": "fail", "answer": f"Failed to fetch data: {str(e)}"}

KEYWORD_ENDPOINT_MAP = {
    "driver": "driver",
    "drivers": "driver",
    "race": "race",
    "races": "race",
    "circuit": "circuit",
    "constructor": "constructor",
    "result": "result",
    "sprint": "sprint",
    "qualifying": "qualifying",
    "pitstop": "pitstop",
    "lap": "lap",
    "driverstanding": "driverstanding",
    "constructorstanding": "constructorstanding",
    "season": "season",
    "status": "status"
}

def get_endpoint_from_query(query: str) -> str:
    query_lower = query.lower()
    for keyword, endpoint in KEYWORD_ENDPOINT_MAP.items():
        if keyword in query_lower:
            return endpoint
    return None

async def query_api_data(user_query: str) -> APIResult:
    # Step 1: Try keyword mapping
    endpoint = get_endpoint_from_query(user_query)
    
    if not endpoint:
        # Step 2: fallback to agent
        try:
            result = await api_agent.run(
                f"User question: '{user_query}'",
                deps=user_query
            )
            if isinstance(result.output, str):
                result_json = json.loads(result.output)
            elif isinstance(result.output, dict):
                result_json = result.output
            else:
                result_json = {}
            endpoint = result_json.get("endpoint")
        except Exception:
            return APIResult(
                endpoint="unknown",
                status="fail",
                answer={"message": "Could not determine endpoint from query."}
            )

    # Step 3: fetch data
    if endpoint:
        fetch_result = await fetch_endpoint_data(None, endpoint)
        if not isinstance(fetch_result.get("answer"), dict):
            fetch_result["answer"] = {"message": str(fetch_result["answer"])}
        return APIResult(**fetch_result)
    else:
        return APIResult(
            endpoint="unknown",
            status="fail",
            answer={"message": "Could not determine endpoint from query."}
        )

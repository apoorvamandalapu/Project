from fastapi import APIRouter
from app.pydantic_models import DriverQuery, DriverResult, APIQuery, APIResult
from app.service import query_driver_data, query_api_data

router = APIRouter()

@router.post("/agent-db", response_model=DriverResult)
async def db_agent(query: DriverQuery):
    return await query_driver_data(query)

@router.post("/agent-api", response_model=APIResult)
async def api_agent(query: APIQuery):
    return await query_api_data(query.query)

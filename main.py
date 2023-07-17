from model import model
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class JSONData(BaseModel):
    startDate: str
    endDate: str
    discreteness: int
    stations: list
    routes: list
    trains: list


@app.get("/")
async def root():
    return {}


@app.post("/")
def post(json_data: JSONData):
    model(json_data.dict())
    return {}

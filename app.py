#Jada Campbell 620141014 PROJECT API
import requests
import json
from datetime import datetime, timedelta, date
from fastapi import FastAPI, Body, Request, HTTPException, status
from fastapi.responses import Response, JSONResponse
import pydantic
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId
import motor.motor_asyncio
import re
from datetime import timedelta

app = FastAPI()
origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://192.168.100.195:8000",
    "http://63.143.93.108:8000",
    "https://i-likedthisprojectngl.onrender.com",
    "https://simple-smart-hub-client.netlify.app"
]

app.add_middleware(                         #instance of middle ware class  
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],                   # HTTP request types like get, post etc. * means all of dem
    allow_headers=["*"],
)

client = motor.motor_asyncio.AsyncIOMotorClient("mongodb+srv://jadasdata:Nilaja2002@cluster0.hj6aecx.mongodb.net/?retryWrites=true&w=majority")
db = client.Project
pydantic.json.ENCODERS_BY_TYPE[ObjectId]=str  


sunset_api_endpoint = "https://api.sunrise-sunset.org/json?lat=18.1096&lng=-77.2975&formatted=0"
sunset_respo = requests.get(sunset_api_endpoint)
sunset_json = sunset_respo.json()
sunset_field = sunset_json['results']['sunset']
sunset_dto= datetime.strptime(sunset_field, "%Y-%m-%dT%H:%M:%S%z")           
sunset_dtoEST = sunset_dto + timedelta(hours =-5)
sunset_time = sunset_dtoEST.strftime("%H:%M:%S")

#Landing page
@app.get("/")
async def jadaissocool():
    return {"The best project in the lineup \u2764\uFE0F"}

#Requests that will be made by the webpage
@app.put("/settings", status_code = 201)        
async def put_data(request: Request):
    info_object = await request.json()
    info_object["pokemon"] = "Arceus"
    
    if info_object["user_light"] == "sunset" :                         #sunset check thing
        info_object["user_light"]= sunset_time
        time_off_dto= sunset_dtoEST + parse_time(info_object["light_duration"])
        info_object["light_time_off"] = time_off_dto.strftime("%H:%M:%S")
        
    else:
        #info_object["user_light_dto"] = datetime.strptime(info_object["user_light"], "%H:%M:%S")     #testing sir
        user_light_to = datetime.strptime(info_object["user_light"], "%H:%M:%S").time()     #making TIME object from user_light parameter
        today = date.today()                                                                #fetching current date
        user_light_dto = datetime.combine(today, user_light_to)                             #attaching current date to user light time
        time_off_dto= user_light_dto + parse_time(info_object["light_duration"])
        info_object["light_time_off"] = datetime.strftime(time_off_dto, "%H:%M:%S")
    
    new_info = await db["Website"].find_one({"pokemon":"Arceus"})   
    if new_info:
        await db["Website"].update_one({"pokemon":"Arceus"}, {"$set": info_object})
    else:
        await db["Website"].insert_one({**info_object, "pokemon":"Arceus"})

    created_info = await db["Website"].find_one({"pokemon":"Arceus"}) 
    if not created_info:
        raise HTTPException(status_code=400, detail= "Bad request!")
    return created_info

@app.get("/graph")
async def plot_graph(request: Request, size: int):
    graph_objects = await db["Embed"].find().sort('_id', -1).to_list(size)
    graph_data_list = []

    for obj in graph_objects:
        temp = obj["temp_reading"]
        pres = obj["presence"]
        datetime = obj["created"]
        graph_data = {"temperature": temp, "presence": pres, "datetime": datetime}
        await db["Graph"].insert_one(graph_data)
        graph_data_list.append(graph_data)

    # Convert ObjectId to string representation
    graph_data_list = [
        {**data, "_id": str(data["_id"])} for data in graph_data_list
    ]
    return JSONResponse(content=graph_data_list)

#Requests from embedded programme
@app.put("/embed", status_code=201)                         
async def embed_put(request: Request):
    data_object = await request.json()
    user_info = await db["Website"].find_one()
    data_object["created"]= datetime.strftime(datetime.now(),"%Y-%m-%dT%H:%M:%S%z")

    usr_light = user_info["user_light"]
    usr_light_to = datetime.strptime(usr_light, "%H:%M:%S").time()
    today = date.today()  
    usr_light_dto = datetime.combine(today, usr_light_to)     

    usr_light_off = user_info["light_time_off"]
    usr_light_off_to = datetime.strptime(usr_light_off, "%H:%M:%S").time()
    usr_light_off_dto = datetime.combine(today,usr_light_off_to)

    if data_object["presence"] == 1:
        if usr_light_dto < datetime.now():
            data_object["light"] = 1
        else:
            data_object["light"] = 0
    else:
        data_object["light"] = 0

    if usr_light_off_dto <= datetime.now():
        data_object["light"] = 0

    if data_object["presence"] == 1:
        if data_object["temp_reading"] > user_info["user_temp"]:
            data_object["fan"] = 1
        else:
            data_object["fan"] = 0
    else:
        data_object["fan"]=0
    new_data = await db["Embed"].insert_one(data_object)
    created_data = await db["Embed"].find_one({"_id": new_data.inserted_id})
    return created_data

@app.get("/embed", status_code=200)
async def embed_get():
    status_object = await db["Embed"].find().sort('_id', -1).to_list(1)
    status_object = [
        {**data, "_id": str(data["_id"])} for data in status_object
    ]
    status_object_json = json.loads(json.dumps(status_object[0]))
    return status_object_json

regex = re.compile(r'((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?')
def parse_time(time_str):
    parts = regex.match(time_str)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {}
    for name, param in parts.items():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params)

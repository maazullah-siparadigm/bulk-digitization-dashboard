import os
from fastapi import FastAPI
from routers import documents
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

app.include_router(documents.router)

host_ip = os.environ.get("HOST_IP", "localhost")

origins = [
    "http://localhost:3000",  # Next.js dev server
    "http://localhost:8082",  # Dockerized / scripted frontend (port 8082)
    f"http://{host_ip}:3000",
    f"http://{host_ip}:8082",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
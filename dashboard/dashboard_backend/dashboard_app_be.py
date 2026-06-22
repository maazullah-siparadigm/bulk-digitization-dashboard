from fastapi import FastAPI
from routers import documents
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

app.include_router(documents.router)

origins = [
    "http://localhost:3000",  # Next.js dev server
    "http://192.168.15.27:3000",  # Next.js dev server
    "http://192.168.15.27:8082",  # Dockerized frontend (host port 8082)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
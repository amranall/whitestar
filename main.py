from fastapi import FastAPI
# from models import create_user_table
from auth import routes as auth_routes
from database import engine
from models import Base
from fastapi.middleware.cors import CORSMiddleware

# import sys
# sys.setrecursionlimit(150)  # Increase the recursion limit

app = FastAPI()
# Include the authentication routes
app.include_router(auth_routes.router, prefix="/auth")
app.include_router(auth_routes.router, prefix="/auth", tags=["clients"])
app.include_router(auth_routes.router, prefix="/auth", tags=["tasks"])

# configure CORS
origins = [
    "http://localhost:3000", # react app
    "http://127.0.0.1:3000",
    "http://localhost:8000", # react app
    # add any other origins
    # "http://localhost:3000/all-users",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    # Create all tables in the database
    Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Community Service API!"}

@app.get("/health")
def health_check():
    return {"status": "OK"}


# Serve the uploads directory as static files
from fastapi.staticfiles import StaticFiles
import os
upload_dir = os.path.join(os.getcwd(), "uploads")
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")
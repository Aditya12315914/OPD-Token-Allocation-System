from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "opd_system")

client = None
database = None

def connect_db():
    global client, database
    client = AsyncIOMotorClient(MONGODB_URL)
    database = client[DATABASE_NAME]
    print(f"Connected to MongoDB: {DATABASE_NAME}")
    return database

def close_db():
    global client
    if client:
        client.close()
        print("MongoDB connection closed")

def get_database():
    return database

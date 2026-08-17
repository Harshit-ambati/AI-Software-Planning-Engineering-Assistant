from pymongo.errors import PyMongoError
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

client: AsyncIOMotorClient | None = None
database: AsyncIOMotorDatabase | None = None


async def connect_to_mongo() -> None:
    global client, database
    pending_client = AsyncIOMotorClient(settings.mongodb_uri, serverSelectionTimeoutMS=500)
    try:
        await pending_client.admin.command("ping")
    except PyMongoError:
        pending_client.close()
        client = None
        database = None
        return

    client = pending_client
    database = client[settings.mongodb_database]


async def close_mongo_connection() -> None:
    global client, database
    if client is not None:
        client.close()
    client = None
    database = None


def get_database() -> AsyncIOMotorDatabase:
    if database is None:
        raise RuntimeError("MongoDB connection has not been initialized.")
    return database


def get_database_or_none() -> AsyncIOMotorDatabase | None:
    return database


def is_mongo_connected() -> bool:
    return client is not None and database is not None

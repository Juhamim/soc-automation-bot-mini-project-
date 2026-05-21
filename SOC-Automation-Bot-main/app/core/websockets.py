import asyncio
import json
import logging
import redis.asyncio as redis
from typing import List
from fastapi import WebSocket
from app.core.config import settings

logger = logging.getLogger(__name__)

# Match the Celery Broker Redis URL
REDIS_URL = settings.CELERY_BROKER_URL
ALERTS_CHANNEL = "alerts_channel"

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.redis_client = None
        self.pubsub = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket connected. Active connections: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info("WebSocket disconnected. Active connections: %d", len(self.active_connections))

    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to a websocket client: {e}")
                self.disconnect(connection)

    async def setup_redis(self):
        try:
            self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            self.pubsub = self.redis_client.pubsub()
            await self.pubsub.subscribe(ALERTS_CHANNEL)
            logger.info("Subscribed to Redis Channel: %s", ALERTS_CHANNEL)
        except Exception as e:
            logger.error("Failed to connect to Redis for Pub/Sub: %s", str(e))

    async def listen_to_redis(self):
        await self.setup_redis()
        if not self.pubsub:
            return
            
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    payload = message["data"]
                    logger.info("Received message from Redis: %s", payload)
                    await self.broadcast(payload)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("Error in Redis listen loop: %s", str(e))
        finally:
            if self.pubsub:
                await self.pubsub.unsubscribe(ALERTS_CHANNEL)
                await self.pubsub.close()
            if self.redis_client:
                await self.redis_client.close()

manager = ConnectionManager()

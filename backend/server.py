from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid
from datetime import datetime
from enum import Enum


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Enums
class TransactionType(str, Enum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CREDIT = "credit" 
    CASHED_OUT = "cashed_out"
    PAID_WITH_CHIPS = "paid_with_chips"

class GameStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"


# Models
class Player(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    current_balance: float = 0.0  # positive = credit owed to player, negative = player owes money
    total_played: float = 0.0
    created_date: datetime = Field(default_factory=datetime.utcnow)

class PlayerCreate(BaseModel):
    name: str

class PlayerUpdate(BaseModel):
    name: Optional[str] = None
    current_balance: Optional[float] = None

class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    player_id: str
    player_name: str
    transaction_type: TransactionType
    amount: float
    description: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TransactionCreate(BaseModel):
    player_id: str
    transaction_type: TransactionType
    amount: float
    description: Optional[str] = None

class Game(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    date: datetime = Field(default_factory=datetime.utcnow)
    players: List[Dict[str, float]] = []  # [{"player_id": "123", "starting_balance": -500}]
    status: GameStatus = GameStatus.ACTIVE
    transactions: List[str] = []  # Transaction IDs
    final_balances: Dict[str, float] = {}  # {"player_id": final_balance}
    created_date: datetime = Field(default_factory=datetime.utcnow)

class GameCreate(BaseModel):
    name: str
    player_ids: List[str]

class GameUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[GameStatus] = None


# Player Routes
@api_router.post("/players", response_model=Player)
async def create_player(player_data: PlayerCreate):
    player = Player(**player_data.dict())
    await db.players.insert_one(player.dict())
    return player

@api_router.get("/players", response_model=List[Player])
async def get_players():
    players = await db.players.find().to_list(1000)
    return [Player(**player) for player in players]

@api_router.get("/players/{player_id}", response_model=Player)
async def get_player(player_id: str):
    player = await db.players.find_one({"id": player_id})
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return Player(**player)

@api_router.put("/players/{player_id}", response_model=Player)
async def update_player(player_id: str, player_update: PlayerUpdate):
    update_data = {k: v for k, v in player_update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data provided for update")
    
    result = await db.players.update_one({"id": player_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Player not found")
    
    updated_player = await db.players.find_one({"id": player_id})
    return Player(**updated_player)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

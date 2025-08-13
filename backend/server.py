from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends, BackgroundTasks
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum
import json
import hmac
import hashlib
# Subscription imports
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, JSON as SQLJSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# PostgreSQL connection for subscriptions
DATABASE_URL = os.getenv("DATABASE_URL")
pg_engine = create_engine(DATABASE_URL) if DATABASE_URL else None
PgSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=pg_engine) if pg_engine else None
PgBase = declarative_base()

# RevenueCat configuration
REVENUECAT_API_KEY = os.getenv("REVENUECAT_API_KEY")
REVENUECAT_WEBHOOK_SECRET = os.getenv("REVENUECAT_WEBHOOK_SECRET", "")

# Subscription models
class SubscriptionUser(PgBase):
    __tablename__ = "subscription_users"
    
    id = Column(Integer, primary_key=True, index=True)
    poker_player_id = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    revenuecat_user_id = Column(String, unique=True, index=True)
    is_premium = Column(Boolean, default=False)
    subscription_platform = Column(String)
    subscription_expires_at = Column(DateTime)
    trial_started_at = Column(DateTime)
    has_used_trial = Column(Boolean, default=False)
    trial_expired = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class WebhookEvent(PgBase):
    __tablename__ = "webhook_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False)
    revenuecat_user_id = Column(String, index=True)
    platform = Column(String)
    product_id = Column(String)
    event_data = Column(SQLJSON)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

class SubscriptionTransaction(PgBase):
    __tablename__ = "subscription_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    revenuecat_user_id = Column(String, index=True)
    transaction_id = Column(String, unique=True)
    product_id = Column(String)
    platform = Column(String)
    purchase_date = Column(DateTime)
    expiration_date = Column(DateTime)
    is_trial = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    amount = Column(Float)
    created_at = Column(DateTime, default=func.now())

# Create subscription tables
if pg_engine:
    PgBase.metadata.create_all(bind=pg_engine)

def get_subscription_db():
    if not PgSessionLocal:
        raise HTTPException(status_code=500, detail="Subscription database not configured")
    db = PgSessionLocal()
    try:
        yield db
    finally:
        db.close()

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
    photo: Optional[str] = None  # Base64 encoded photo
    created_date: datetime = Field(default_factory=datetime.utcnow)

class PlayerCreate(BaseModel):
    name: str
    photo: Optional[str] = None

class PlayerUpdate(BaseModel):
    name: Optional[str] = None
    current_balance: Optional[float] = None
    photo: Optional[str] = None

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
    players: List[Dict[str, Any]] = []  # [{"player_id": "123", "starting_balance": -500, "chips_in_game": 0}]
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

@api_router.delete("/players/{player_id}")
async def delete_player(player_id: str):
    # Check if player is in any active games
    active_games = await db.games.find({"status": GameStatus.ACTIVE}).to_list(1000)
    for game in active_games:
        if any(p["player_id"] == player_id for p in game["players"]):
            raise HTTPException(status_code=400, detail="Cannot delete player who is in an active game")
    
    result = await db.players.delete_one({"id": player_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Player not found")
    
    return {"message": "Player deleted successfully"}

# Game Routes
@api_router.post("/games", response_model=Game)
async def create_game(game_data: GameCreate):
    # Get players and their current balances
    players_with_balances = []
    for player_id in game_data.player_ids:
        player = await db.players.find_one({"id": player_id})
        if not player:
            raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
        players_with_balances.append({
            "player_id": player_id,
            "player_name": player["name"],
            "starting_balance": player["current_balance"],
            "chips_in_game": 0.0  # Start fresh - no chips carried over from previous games
        })
    
    game = Game(name=game_data.name, players=players_with_balances)
    await db.games.insert_one(game.dict())
    return game

@api_router.get("/games", response_model=List[Game])
async def get_games():
    games = await db.games.find().sort("created_date", -1).to_list(1000)
    return [Game(**game) for game in games]

@api_router.get("/games/{game_id}", response_model=Game)
async def get_game(game_id: str):
    game = await db.games.find_one({"id": game_id})
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return Game(**game)

@api_router.put("/games/{game_id}", response_model=Game)
async def update_game(game_id: str, game_update: GameUpdate):
    update_data = {k: v for k, v in game_update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data provided for update")
    
    result = await db.games.update_one({"id": game_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Game not found")
    
    updated_game = await db.games.find_one({"id": game_id})
    return Game(**updated_game)


# Transaction Routes
@api_router.post("/games/{game_id}/transactions", response_model=Transaction)
async def create_transaction(game_id: str, transaction_data: TransactionCreate):
    # Verify game exists and is active
    game = await db.games.find_one({"id": game_id})
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.get("status") != GameStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Cannot add transactions to closed game")
    
    # Get player info
    player = await db.players.find_one({"id": transaction_data.player_id})
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Create transaction
    transaction = Transaction(
        game_id=game_id,
        player_id=transaction_data.player_id,
        player_name=player["name"],
        **transaction_data.dict(exclude={"player_id"})
    )
    
    # Calculate balance change and total_played change based on transaction type
    balance_change = 0.0
    total_played_change = 0.0
    
    if transaction_data.transaction_type == TransactionType.CASH:
        # Cash purchase - no balance change, but adds to total played
        balance_change = 0.0
        total_played_change = transaction_data.amount
    elif transaction_data.transaction_type == TransactionType.BANK_TRANSFER:
        # Bank transfer purchase - no balance change, but adds to total played
        balance_change = 0.0
        total_played_change = transaction_data.amount
    elif transaction_data.transaction_type == TransactionType.CREDIT:
        # Credit - player receives chips on credit, creates debt (negative balance) and adds to total played
        balance_change = -transaction_data.amount
        total_played_change = transaction_data.amount
    elif transaction_data.transaction_type == TransactionType.CASHED_OUT:
        # Cashed out - player cashes out chips they won (POSITIVE for player)
        if transaction_data.amount <= 0:
            raise HTTPException(status_code=400, detail="Cash out amount must be greater than 0")
        balance_change = transaction_data.amount  # POSITIVE - increases player's credit balance
        total_played_change = 0.0
    elif transaction_data.transaction_type == TransactionType.PAID_WITH_CHIPS:
        # Paid with chips - reduces debt or creates positive balance
        balance_change = transaction_data.amount
        total_played_change = 0.0
    
    # Update player balance and total played
    new_balance = player["current_balance"] + balance_change
    new_total_played = player["total_played"] + total_played_change
    
    await db.players.update_one(
        {"id": transaction_data.player_id}, 
        {"$set": {
            "current_balance": new_balance,
            "total_played": new_total_played
        }}
    )
    
    # Update chips_in_game for this specific game (if chips were added or removed)
    if total_played_change > 0:
        # Add chips to the game (Cash, Bank Transfer, Credit)
        await db.games.update_one(
            {"id": game_id, "players.player_id": transaction_data.player_id},
            {"$inc": {"players.$.chips_in_game": total_played_change}}
        )
    elif transaction_data.transaction_type == TransactionType.CASHED_OUT:
        # Remove chips from the game when player cashes out
        await db.games.update_one(
            {"id": game_id, "players.player_id": transaction_data.player_id},
            {"$inc": {"players.$.chips_in_game": -transaction_data.amount}}
        )
    
    # Save transaction
    await db.transactions.insert_one(transaction.dict())
    
    # Add transaction to game
    await db.games.update_one(
        {"id": game_id}, 
        {"$push": {"transactions": transaction.id}}
    )
    
    return transaction

@api_router.get("/games/{game_id}/transactions", response_model=List[Transaction])
async def get_game_transactions(game_id: str):
    transactions = await db.transactions.find({"game_id": game_id}).sort("timestamp", 1).to_list(1000)
    return [Transaction(**transaction) for transaction in transactions]

class AddPlayerRequest(BaseModel):
    player_id: str

@api_router.post("/games/{game_id}/add-player")
async def add_player_to_game(game_id: str, request: AddPlayerRequest):
    # Get game
    game = await db.games.find_one({"id": game_id})
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.get("status") != GameStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Cannot add players to closed game")
    
    # Check if player already in game
    existing_player_ids = [p["player_id"] for p in game["players"]]
    if request.player_id in existing_player_ids:
        raise HTTPException(status_code=400, detail="Player already in this game")
    
    # Get player info
    player = await db.players.find_one({"id": request.player_id})
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Add player to game
    new_player_info = {
        "player_id": request.player_id,
        "player_name": player["name"],
        "starting_balance": player["current_balance"],
        "chips_in_game": 0.0  # Initialize chips in game
    }
    
    await db.games.update_one(
        {"id": game_id},
        {"$push": {"players": new_player_info}}
    )
    
    return {"message": "Player added to game successfully", "player": new_player_info}


@api_router.post("/games/{game_id}/close")
async def close_game(game_id: str):
    # Get game
    game = await db.games.find_one({"id": game_id})
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.get("status") == GameStatus.CLOSED:
        raise HTTPException(status_code=400, detail="Game is already closed")
    
    # Get final balances for all players in the game
    final_balances = {}
    for player_info in game["players"]:
        player_id = player_info["player_id"]
        player = await db.players.find_one({"id": player_id})
        if player:
            final_balances[player_id] = player["current_balance"]
    
    # Update game status and final balances
    await db.games.update_one(
        {"id": game_id}, 
        {
            "$set": {
                "status": GameStatus.CLOSED,
                "final_balances": final_balances
            }
        }
    )
    
    return {"message": "Game closed successfully", "final_balances": final_balances}


# Dashboard/Stats Routes
@api_router.get("/dashboard")
async def get_dashboard():
    # Get active games count
    active_games = await db.games.count_documents({"status": GameStatus.ACTIVE})
    
    # Get total players
    total_players = await db.players.count_documents({})
    
    # Get players with positive balances (money owed to players)
    players_with_credit = await db.players.find({"current_balance": {"$gt": 0}}).to_list(1000)
    total_credit_owed = sum(player["current_balance"] for player in players_with_credit)
    
    # Get players with negative balances (money owed by players)  
    players_with_debt = await db.players.find({"current_balance": {"$lt": 0}}).to_list(1000)
    total_debt_owed = sum(abs(player["current_balance"]) for player in players_with_debt)
    
    # Get recent transactions
    recent_transactions = await db.transactions.find().sort("timestamp", -1).limit(10).to_list(10)
    
    return {
        "active_games": active_games,
        "total_players": total_players,
        "total_credit_owed": total_credit_owed,
        "total_debt_owed": total_debt_owed,
        "recent_transactions": [Transaction(**t) for t in recent_transactions]
    }


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

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

# PostgreSQL connection for subscriptions (disabled for demo)
DATABASE_URL = os.getenv("DATABASE_URL")
pg_engine = None
PgSessionLocal = None
print("PostgreSQL disabled for demo, using in-memory storage for subscriptions")

PgBase = declarative_base()

# In-memory storage for demo
subscription_users_memory = {}
webhook_events_memory = []
subscription_transactions_memory = []

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
    """Get subscription database session or None if not available."""
    if not PgSessionLocal:
        return None
    db = PgSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Utility functions for in-memory storage
def get_user_from_memory(player_id: str):
    """Get user from memory storage."""
    return subscription_users_memory.get(player_id)

def save_user_to_memory(player_id: str, user_data: dict):
    """Save user to memory storage."""
    subscription_users_memory[player_id] = user_data
    return user_data

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

# Subscription Pydantic models
class SubscriptionUserCreate(BaseModel):
    poker_player_id: str
    email: str

class SubscriptionUserResponse(BaseModel):
    id: int
    poker_player_id: str
    email: str
    is_premium: bool
    subscription_platform: Optional[str]
    subscription_expires_at: Optional[datetime]
    has_used_trial: bool
    trial_expired: bool
    
    class Config:
        from_attributes = True

class SubscriptionStatus(BaseModel):
    is_premium: bool
    days_remaining: Optional[int] = None
    is_trial: bool = False
    can_start_trial: bool = True

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
    
    # Update chips_in_game for this specific game 
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
    elif transaction_data.transaction_type == TransactionType.PAID_WITH_CHIPS:
        # Remove chips from the game when player pays with chips (CRITICAL FIX)
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
    """Get dashboard statistics."""
    try:
        # Basic dashboard stats
        active_games = await db.games.count_documents({"status": GameStatus.ACTIVE})
        total_players = await db.players.count_documents({})
        
        # Calculate total credit owed (positive balances - money owed TO players)
        total_credit_pipeline = [
            {"$match": {"current_balance": {"$gt": 0}}},
            {"$group": {"_id": None, "total": {"$sum": "$current_balance"}}}
        ]
        credit_result = await db.players.aggregate(total_credit_pipeline).to_list(1)
        total_credit_owed = credit_result[0]["total"] if credit_result else 0
        
        # Calculate total debt owed (negative balances - money owed BY players)
        total_debt_pipeline = [
            {"$match": {"current_balance": {"$lt": 0}}},
            {"$group": {"_id": None, "total": {"$sum": "$current_balance"}}}
        ]
        debt_result = await db.players.aggregate(total_debt_pipeline).to_list(1)
        total_debt_owed = abs(debt_result[0]["total"]) if debt_result else 0
        
        # Get recent transactions (last 10)
        recent_transactions = await db.transactions.find().sort("timestamp", -1).limit(10).to_list(10)
        
        return {
            "active_games": active_games,
            "total_players": total_players,
            "total_credit_owed": total_credit_owed,
            "total_debt_owed": total_debt_owed,
            "recent_transactions": [Transaction(**t) for t in recent_transactions]
        }
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        return {
            "active_games": 0,
            "total_players": 0,
            "total_credit_owed": 0.0,
            "total_debt_owed": 0.0,
            "recent_transactions": []
        }

# Subscription utility functions
def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify RevenueCat webhook signature for security."""
    if not REVENUECAT_WEBHOOK_SECRET:
        logger.warning("Webhook secret not configured")
        return False
    
    expected_signature = hmac.new(
        REVENUECAT_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected_signature}", signature)

def create_revenuecat_user_id(player_id: str) -> str:
    """Create a RevenueCat user ID from player ID."""
    return f"player_{player_id}"

def check_trial_eligibility(user: SubscriptionUser) -> bool:
    """Check if user is eligible for free trial."""
    return not user.has_used_trial and not user.trial_expired

def calculate_days_remaining(expires_at: datetime) -> int:
    """Calculate days remaining in subscription."""
    if not expires_at:
        return 0
    now = datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    delta = expires_at - now
    return max(0, delta.days)

# Subscription Routes
@api_router.post("/subscription/create-user", response_model=SubscriptionUserResponse)
async def create_subscription_user(
    user_data: SubscriptionUserCreate,
    pg_db: Session = Depends(get_subscription_db)
):
    """Create a new subscription user linked to a poker player."""
    # Check if user already exists
    existing_user = pg_db.query(SubscriptionUser).filter(
        SubscriptionUser.poker_player_id == user_data.poker_player_id
    ).first()
    
    if existing_user:
        return existing_user
    
    # Create RevenueCat user ID
    revenuecat_user_id = create_revenuecat_user_id(user_data.poker_player_id)
    
    # Create new subscription user
    new_user = SubscriptionUser(
        poker_player_id=user_data.poker_player_id,
        email=user_data.email,
        revenuecat_user_id=revenuecat_user_id
    )
    
    pg_db.add(new_user)
    pg_db.commit()
    pg_db.refresh(new_user)
    
    return new_user

@api_router.get("/subscription/status/{player_id}")
async def get_subscription_status(player_id: str):
    """Get subscription status for a player."""
    try:
        # Use memory storage
        user = get_user_from_memory(player_id)
        if user:
            is_premium = user.get("is_premium", False)
            expires_at = user.get("subscription_expires_at")
            
            if expires_at and isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                if expires_at <= now:
                    is_premium = False
                    user["is_premium"] = False
                    save_user_to_memory(player_id, user)
            
            days_remaining = 0
            if expires_at and is_premium:
                now = datetime.now(timezone.utc)
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                delta = expires_at - now
                days_remaining = max(0, delta.days)
            
            is_trial = user.get("is_trial", False)
            
            return {
                "is_premium": is_premium,
                "days_remaining": days_remaining,
                "is_trial": is_trial,
                "can_start_trial": not user.get("has_used_trial", False)
            }
        
        # User doesn't exist, eligible for trial
        return {
            "is_premium": False,
            "days_remaining": 0,
            "is_trial": False,
            "can_start_trial": True
        }
        
    except Exception as e:
        logger.error(f"Error getting subscription status: {str(e)}")
        return {
            "is_premium": False,
            "days_remaining": 0,
            "is_trial": False,
            "can_start_trial": True
        }

@api_router.post("/subscription/start-trial/{player_id}")
async def start_free_trial(player_id: str):
    """Start free trial for a player (7 days)."""
    try:
        now = datetime.now(timezone.utc)
        trial_end = now + timedelta(days=7)
        
        # Use memory storage
        user = get_user_from_memory(player_id)
        if not user:
            user = {
                "poker_player_id": player_id,
                "email": f"{player_id}@temp.com",
                "is_premium": False,
                "has_used_trial": False,
            }
        
        if user.get("has_used_trial", False):
            raise HTTPException(status_code=400, detail="User not eligible for trial")
        
        user.update({
            "is_premium": True,
            "trial_started_at": now.isoformat(),
            "subscription_expires_at": trial_end.isoformat(),
            "has_used_trial": True,
            "subscription_platform": "trial",
            "is_trial": True
        })
        
        save_user_to_memory(player_id, user)
        
        return {
            "message": "Free trial started successfully",
            "trial_ends_at": trial_end.isoformat(),
            "days_remaining": 7
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting trial: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start trial")

@api_router.post("/webhooks/revenuecat")
async def handle_revenuecat_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    pg_db: Session = Depends(get_subscription_db)
):
    """Handle RevenueCat webhook events."""
    try:
        # Get raw payload for signature verification
        payload = await request.body()
        signature = request.headers.get("authorization", "")
        
        # Verify webhook signature
        if REVENUECAT_WEBHOOK_SECRET and not verify_webhook_signature(payload, signature):
            logger.warning("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse webhook data
        webhook_data = json.loads(payload.decode())
        event_type = webhook_data.get("type")
        app_user_id = webhook_data.get("app_user_id")
        
        # Log webhook event
        webhook_event = WebhookEvent(
            event_type=event_type,
            revenuecat_user_id=app_user_id,
            platform=webhook_data.get("store", "unknown"),
            product_id=webhook_data.get("product_id"),
            event_data=webhook_data
        )
        pg_db.add(webhook_event)
        pg_db.commit()
        
        # Process webhook event
        background_tasks.add_task(process_webhook_event, webhook_data, pg_db)
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

def process_webhook_event(webhook_data: dict, pg_db: Session):
    """Process RevenueCat webhook events and update user subscriptions."""
    try:
        event_type = webhook_data.get("type")
        app_user_id = webhook_data.get("app_user_id")
        
        if not app_user_id:
            logger.warning("No app_user_id in webhook data")
            return
        
        # Get user
        user = pg_db.query(SubscriptionUser).filter(
            SubscriptionUser.revenuecat_user_id == app_user_id
        ).first()
        
        if not user:
            logger.warning(f"User not found for RevenueCat ID: {app_user_id}")
            return
        
        # Process based on event type
        if event_type == "INITIAL_PURCHASE":
            handle_initial_purchase(webhook_data, user, pg_db)
        elif event_type == "RENEWAL":
            handle_renewal(webhook_data, user, pg_db)
        elif event_type == "CANCELLATION":
            handle_cancellation(webhook_data, user, pg_db)
        elif event_type == "EXPIRATION":
            handle_expiration(webhook_data, user, pg_db)
        
        pg_db.commit()
        logger.info(f"Processed webhook event {event_type} for user {app_user_id}")
        
    except Exception as e:
        logger.error(f"Error processing webhook event: {str(e)}")
        pg_db.rollback()

def handle_initial_purchase(webhook_data: dict, user: SubscriptionUser, pg_db: Session):
    """Handle initial subscription purchase events."""
    entitlements = webhook_data.get("entitlements", {})
    
    # Check if premium entitlement is active
    premium_entitlement = entitlements.get("premium")
    if premium_entitlement and premium_entitlement.get("expires_date"):
        user.is_premium = True
        expires_date = premium_entitlement["expires_date"]
        user.subscription_expires_at = datetime.fromisoformat(
            expires_date.replace("Z", "+00:00")
        )
        user.subscription_platform = webhook_data.get("store", "unknown")
        
        # Create transaction record
        transaction = SubscriptionTransaction(
            user_id=user.id,
            revenuecat_user_id=user.revenuecat_user_id,
            transaction_id=webhook_data.get("transaction_id"),
            product_id=webhook_data.get("product_id"),
            platform=webhook_data.get("store"),
            purchase_date=datetime.now(timezone.utc),
            expiration_date=user.subscription_expires_at,
            is_trial=premium_entitlement.get("is_sandbox", False),
            is_active=True,
            amount=2.0  # $2 monthly subscription
        )
        pg_db.add(transaction)

def handle_renewal(webhook_data: dict, user: SubscriptionUser, pg_db: Session):
    """Handle subscription renewal events."""
    entitlements = webhook_data.get("entitlements", {})
    premium_entitlement = entitlements.get("premium")
    
    if premium_entitlement:
        expires_date = premium_entitlement["expires_date"]
        user.subscription_expires_at = datetime.fromisoformat(
            expires_date.replace("Z", "+00:00")
        )
        user.is_premium = True

def handle_cancellation(webhook_data: dict, user: SubscriptionUser, pg_db: Session):
    """Handle subscription cancellation events."""
    # User keeps access until expiration date
    logger.info(f"Subscription cancelled for user {user.revenuecat_user_id}, access until {user.subscription_expires_at}")

def handle_expiration(webhook_data: dict, user: SubscriptionUser, pg_db: Session):
    """Handle subscription expiration events."""
    user.is_premium = False
    user.subscription_expires_at = None
    user.subscription_platform = None
    
    # Mark transactions as inactive
    transactions = pg_db.query(SubscriptionTransaction).filter(
        SubscriptionTransaction.revenuecat_user_id == user.revenuecat_user_id,
        SubscriptionTransaction.is_active == True
    ).all()
    
    for transaction in transactions:
        transaction.is_active = False


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

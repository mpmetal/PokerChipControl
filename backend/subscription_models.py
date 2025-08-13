from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class SubscriptionUser(Base):
    __tablename__ = "subscription_users"
    
    id = Column(Integer, primary_key=True, index=True)
    # Link to poker player
    poker_player_id = Column(String, index=True)  # UUID from MongoDB player
    email = Column(String, unique=True, index=True)
    # RevenueCat integration
    revenuecat_user_id = Column(String, unique=True, index=True)
    # Subscription status
    is_premium = Column(Boolean, default=False)
    subscription_platform = Column(String)  # 'android', 'ios', or None
    subscription_expires_at = Column(DateTime)
    trial_started_at = Column(DateTime)
    # Trial status
    has_used_trial = Column(Boolean, default=False)
    trial_expired = Column(Boolean, default=False)
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False)
    revenuecat_user_id = Column(String, index=True)
    platform = Column(String)
    product_id = Column(String)
    event_data = Column(JSON)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    
class SubscriptionTransaction(Base):
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
    amount = Column(Float)  # Amount in USD
    created_at = Column(DateTime, default=func.now())

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_subscription_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("Creating subscription tables...")
    create_tables()
    print("Tables created successfully!")
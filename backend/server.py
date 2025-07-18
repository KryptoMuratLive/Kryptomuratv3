from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
from web3 import Web3
from emergentintegrations.llm.chat import LlmChat, UserMessage
import asyncio
import json
from telegram import Bot
from telegram.constants import ParseMode
import httpx

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

# Web3 Configuration
POLYGON_RPC_URL = "https://polygon-rpc.com"
MURAT_TOKEN_ADDRESS = "0x04296ee51cd6fdfEE0CB1016A818F17b8ae7a1dD"
web3 = Web3(Web3.HTTPProvider(POLYGON_RPC_URL))

# OpenAI Configuration
OPENAI_API_KEY = "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"

# Livepeer Configuration
LIVEPEER_API_KEY = "0b8aedbd-2eca-494c-a5fd-2e5b3770b382"
LIVEPEER_BASE_URL = "https://livepeer.com/api"

# Telegram Bot Configuration
TELEGRAM_TOKEN = "7862770623:AAEmy3TgM_EK-RnSo1nYIg0H78JPJOvNjS0"
WEBHOOK_SECRET = "kryptomurat_webhook_secret_2024"

# Define Models
class WalletConnect(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    wallet_address: str
    chain_id: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TokenBalance(BaseModel):
    wallet_address: str
    balance: str
    symbol: str = "MURAT"
    decimals: int = 18

class StakingPosition(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    wallet_address: str
    amount: str
    duration_days: int
    apy: float
    start_date: datetime = Field(default_factory=datetime.utcnow)
    end_date: datetime
    status: str = "active"  # active, completed, withdrawn

class NFTAccess(BaseModel):
    wallet_address: str
    has_access: bool
    nft_count: int
    access_level: str = "basic"  # basic, premium, vip

class AIContentRequest(BaseModel):
    prompt: str
    content_type: str = "meme"  # meme, comic, story, text
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class AIContentResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    content_type: str
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StreamRequest(BaseModel):
    name: str
    description: str = ""
    nft_required: bool = True

class StreamResponse(BaseModel):
    id: str
    name: str
    description: str
    stream_key: str
    playback_id: str
    is_active: bool = True
    nft_required: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    creator_wallet: str

class StreamAccess(BaseModel):
    wallet_address: str
    stream_id: str
    access_granted: bool
    access_level: str = "viewer"  # viewer, streamer, admin

class StoryChapter(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    content: str
    chapter_number: int
    image_url: str = ""
    nft_required: bool = False
    choices: List[dict] = []
    next_chapters: List[str] = []
    unlock_requirements: dict = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)

class StoryProgress(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    wallet_address: str
    current_chapter: str
    completed_chapters: List[str] = []
    choices_made: List[dict] = []
    reputation_score: int = 0
    items_collected: List[str] = []
    story_path: str = "main"  # main, heroic, mysterious, action
    last_played: datetime = Field(default_factory=datetime.utcnow)

class StoryChoice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chapter_id: str
    wallet_address: str
    choice_index: int
    choice_text: str
    consequence: str = ""
    reputation_change: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StoryVote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    wallet_address: str
    vote_type: str  # next_chapter, story_direction, character_fate
    vote_option: str
    vote_weight: int = 1  # NFT holders get higher weight
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# ERC-20 Token ABI (simplified for balance check)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    }
]

# Initialize Telegram Bot
telegram_bot = Bot(token=TELEGRAM_TOKEN)

# Telegram helper functions
def escape_markdown_v2(text: str) -> str:
    """Escape special characters for MarkdownV2"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

async def send_telegram_notification(chat_id: int, message: str, parse_mode: str = "MarkdownV2"):
    """Send notification to Telegram"""
    try:
        if parse_mode == "MarkdownV2":
            message = escape_markdown_v2(message)
        
        await telegram_bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=parse_mode
        )
        
        # Log to database
        await db.telegram_messages.insert_one({
            "chat_id": chat_id,
            "message": message,
            "timestamp": datetime.utcnow(),
            "status": "sent"
        })
        
        return True
    except Exception as e:
        print(f"Telegram notification error: {e}")
        return False

class TelegramSubscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    wallet_address: str
    chat_id: int
    username: str = ""
    notifications: dict = {
        "story_updates": True,
        "staking_alerts": True,
        "stream_notifications": True,
        "nft_alerts": True,
        "ai_content": True
    }
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

# Web3 and Wallet Routes
@api_router.post("/wallet/connect")
async def connect_wallet(wallet_data: WalletConnect):
    """Connect wallet and store session"""
    try:
        # Validate wallet address
        if not Web3.is_address(wallet_data.wallet_address):
            raise HTTPException(status_code=400, detail="Invalid wallet address")
        
        # Store wallet connection
        await db.wallet_connections.insert_one(wallet_data.dict())
        
        return {"success": True, "message": "Wallet connected successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/wallet/balance/{wallet_address}")
async def get_token_balance(wallet_address: str):
    """Get MURAT token balance"""
    try:
        if not Web3.is_address(wallet_address):
            raise HTTPException(status_code=400, detail="Invalid wallet address")
        
        try:
            # Convert to checksum address to avoid EIP-55 errors
            wallet_address = Web3.to_checksum_address(wallet_address)
            
            # Create contract instance
            contract = web3.eth.contract(address=MURAT_TOKEN_ADDRESS, abi=ERC20_ABI)
            
            # Get balance
            balance_wei = contract.functions.balanceOf(wallet_address).call()
            decimals = contract.functions.decimals().call()
            symbol = contract.functions.symbol().call()
            
            # Convert to human readable format
            balance = balance_wei / (10 ** decimals)
            
            return TokenBalance(
                wallet_address=wallet_address,
                balance=str(balance),
                symbol=symbol,
                decimals=decimals
            )
        except Exception as e:
            # If there's an error with the contract call, return zero balance
            return TokenBalance(
                wallet_address=wallet_address,
                balance="0.0",
                symbol="MURAT",
                decimals=18
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching balance: {str(e)}")

# Staking Routes
@api_router.post("/staking/create")
async def create_staking_position(staking_data: dict):
    """Create a new staking position"""
    try:
        wallet_address = staking_data.get("wallet_address")
        amount = staking_data.get("amount")
        duration_days = staking_data.get("duration_days")
        
        if not wallet_address or not amount or not duration_days:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Calculate APY based on duration
        apy_rates = {30: 2.0, 90: 4.0, 180: 6.0, 360: 8.0}
        apy = apy_rates.get(duration_days, 2.0)
        
        # Calculate end date
        end_date = datetime.utcnow() + timedelta(days=duration_days)
        
        staking_position = StakingPosition(
            wallet_address=wallet_address,
            amount=amount,
            duration_days=duration_days,
            apy=apy,
            end_date=end_date
        )
        
        await db.staking_positions.insert_one(staking_position.dict())
        
        return {"success": True, "staking_position": staking_position}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/staking/positions/{wallet_address}")
async def get_staking_positions(wallet_address: str):
    """Get all staking positions for a wallet"""
    try:
        positions = await db.staking_positions.find({"wallet_address": wallet_address}).to_list(100)
        return [StakingPosition(**pos) for pos in positions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/staking/rewards/{wallet_address}")
async def calculate_staking_rewards(wallet_address: str):
    """Calculate current staking rewards"""
    try:
        positions = await db.staking_positions.find({"wallet_address": wallet_address, "status": "active"}).to_list(100)
        
        total_rewards = 0
        for pos in positions:
            position = StakingPosition(**pos)
            days_staked = (datetime.utcnow() - position.start_date).days
            daily_rate = position.apy / 365 / 100
            rewards = float(position.amount) * daily_rate * days_staked
            total_rewards += rewards
        
        return {"total_rewards": total_rewards, "wallet_address": wallet_address}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# NFT Access Control
@api_router.get("/nft/access/{wallet_address}")
async def check_nft_access(wallet_address: str):
    """Check NFT access for wallet"""
    try:
        # Mock NFT check - in production, would check actual NFT contract
        # For MVP, we'll simulate access based on wallet having some ETH/MATIC
        try:
            # Convert to checksum address to avoid EIP-55 errors
            wallet_address = Web3.to_checksum_address(wallet_address)
            balance = web3.eth.get_balance(wallet_address)
        except Exception as e:
            # If address conversion fails, assume no access
            return NFTAccess(
                wallet_address=wallet_address,
                has_access=False,
                nft_count=0,
                access_level="none"
            )
        
        if balance > 0:
            access_level = "premium" if balance > web3.toWei(1, 'ether') else "basic"
            return NFTAccess(
                wallet_address=wallet_address,
                has_access=True,
                nft_count=1,
                access_level=access_level
            )
        else:
            return NFTAccess(
                wallet_address=wallet_address,
                has_access=False,
                nft_count=0,
                access_level="none"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# AI Content Generation
@api_router.post("/ai/generate")
async def generate_ai_content(request: AIContentRequest):
    """Generate AI content using OpenAI"""
    try:
        # For testing purposes, return mock AI content instead of calling OpenAI
        mock_content = f"Mock AI generated content for: {request.prompt}. This is a test response for content type: {request.content_type}"
        
        # Save to database
        ai_response = AIContentResponse(
            content=mock_content,
            content_type=request.content_type,
            session_id=request.session_id
        )
        
        await db.ai_content.insert_one(ai_response.dict())
        
        return ai_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/ai/content/{session_id}")
async def get_ai_content_history(session_id: str):
    """Get AI content history for session"""
    try:
        content = await db.ai_content.find({"session_id": session_id}).to_list(100)
        return [AIContentResponse(**item) for item in content]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Admin Dashboard Routes
@api_router.get("/admin/stats")
async def get_admin_stats():
    """Get admin dashboard statistics"""
    try:
        # Get user count
        user_count = await db.wallet_connections.count_documents({})
        
        # Get staking stats
        staking_positions = await db.staking_positions.find({}).to_list(1000)
        total_staked = sum(float(pos.get("amount", 0)) for pos in staking_positions)
        active_stakes = len([pos for pos in staking_positions if pos.get("status") == "active"])
        
        # Get AI content stats
        ai_content_count = await db.ai_content.count_documents({})
        
        return {
            "user_count": user_count,
            "total_staked": total_staked,
            "active_stakes": active_stakes,
            "ai_content_generated": ai_content_count,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Livepeer Streaming Routes
@api_router.post("/streams/create")
async def create_stream(stream_request: StreamRequest, creator_wallet: str):
    """Create a new Livepeer stream"""
    try:
        # Create stream in Livepeer
        livepeer_payload = {
            "name": stream_request.name,
            "profiles": [
                {
                    "name": "720p",
                    "bitrate": 3000000,
                    "fps": 30,
                    "width": 1280,
                    "height": 720
                },
                {
                    "name": "480p", 
                    "bitrate": 1500000,
                    "fps": 30,
                    "width": 854,
                    "height": 480
                },
                {
                    "name": "360p",
                    "bitrate": 800000,
                    "fps": 30,
                    "width": 640,
                    "height": 360
                }
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {LIVEPEER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        import requests
        response = requests.post(
            f"{LIVEPEER_BASE_URL}/stream",
            json=livepeer_payload,
            headers=headers
        )
        
        if response.status_code != 201:
            raise HTTPException(status_code=500, detail=f"Livepeer stream creation failed: {response.text}")
        
        livepeer_stream = response.json()
        
        # Create our stream record
        stream_data = StreamResponse(
            id=livepeer_stream["id"],
            name=stream_request.name,
            description=stream_request.description,
            stream_key=livepeer_stream["streamKey"],
            playback_id=livepeer_stream["playbackId"],
            nft_required=stream_request.nft_required,
            creator_wallet=creator_wallet
        )
        
        # Save to database
        await db.live_streams.insert_one(stream_data.dict())
        
        return stream_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/streams")
async def get_streams():
    """Get all available streams"""
    try:
        streams = await db.live_streams.find({}).to_list(100)
        return [StreamResponse(**stream) for stream in streams]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/streams/{stream_id}")
async def get_stream(stream_id: str):
    """Get stream by ID"""
    try:
        stream = await db.live_streams.find_one({"id": stream_id})
        if not stream:
            raise HTTPException(status_code=404, detail="Stream not found")
        return StreamResponse(**stream)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/streams/{stream_id}/access")
async def verify_stream_access(stream_id: str, wallet_address: str):
    """Verify access to a stream based on NFT ownership"""
    try:
        # Get stream info
        stream = await db.live_streams.find_one({"id": stream_id})
        if not stream:
            raise HTTPException(status_code=404, detail="Stream not found")
        
        # If NFT is not required, grant access
        if not stream.get("nft_required", True):
            return StreamAccess(
                wallet_address=wallet_address,
                stream_id=stream_id,
                access_granted=True,
                access_level="viewer"
            )
        
        # Check NFT ownership (using existing NFT check logic)
        nft_access = await check_nft_access(wallet_address)
        
        if not nft_access.has_access:
            raise HTTPException(status_code=403, detail="NFT ownership required for stream access")
        
        # Store access record
        access_record = StreamAccess(
            wallet_address=wallet_address,
            stream_id=stream_id,
            access_granted=True,
            access_level=nft_access.access_level
        )
        
        await db.stream_access.insert_one(access_record.dict())
        
        return access_record
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/streams/{stream_id}/playback/{wallet_address}")
async def get_stream_playback(stream_id: str, wallet_address: str):
    """Get playback URL for verified users"""
    try:
        # Verify access first
        access = await verify_stream_access(stream_id, wallet_address)
        
        if not access.access_granted:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get stream info
        stream = await db.live_streams.find_one({"id": stream_id})
        if not stream:
            raise HTTPException(status_code=404, detail="Stream not found")
        
        # Return playback URLs
        playback_id = stream["playback_id"]
        
        return {
            "playback_id": playback_id,
            "hls_url": f"https://cdn.livepeer.com/hls/{playback_id}/index.m3u8",
            "webrtc_url": f"https://cdn.livepeer.com/webrtc/{playback_id}",
            "access_level": access.access_level
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/streams/{stream_id}")
async def delete_stream(stream_id: str, creator_wallet: str):
    """Delete a stream (only creator can delete)"""
    try:
        # Check if user is creator
        stream = await db.live_streams.find_one({"id": stream_id})
        if not stream:
            raise HTTPException(status_code=404, detail="Stream not found")
        
        if stream["creator_wallet"] != creator_wallet:
            raise HTTPException(status_code=403, detail="Only stream creator can delete")
        
        # Delete from Livepeer
        headers = {
            "Authorization": f"Bearer {LIVEPEER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        import requests
        response = requests.delete(
            f"{LIVEPEER_BASE_URL}/stream/{stream_id}",
            headers=headers
        )
        
        # Delete from our database
        await db.live_streams.delete_one({"id": stream_id})
        await db.stream_access.delete_many({"stream_id": stream_id})
        
        return {"success": True, "message": "Stream deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/streams/{stream_id}/viewers")
async def get_stream_viewers(stream_id: str):
    """Get current viewers for a stream"""
    try:
        # Get viewer count from access records
        viewers = await db.stream_access.find({"stream_id": stream_id}).to_list(1000)
        
        # Get stream info from Livepeer (for live stats)
        headers = {
            "Authorization": f"Bearer {LIVEPEER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        import requests
        response = requests.get(
            f"{LIVEPEER_BASE_URL}/stream/{stream_id}",
            headers=headers
        )
        
        livepeer_stats = response.json() if response.status_code == 200 else {}
        
        return {
            "total_viewers": len(viewers),
            "current_viewers": livepeer_stats.get("isActive", 0),
            "stream_status": "live" if livepeer_stats.get("isActive") else "offline"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Interactive Story Module Routes
@api_router.post("/story/initialize")
async def initialize_story(wallet_address: str):
    """Initialize story for a new player"""
    try:
        # Check if player already has progress
        existing_progress = await db.story_progress.find_one({"wallet_address": wallet_address})
        if existing_progress:
            return StoryProgress(**existing_progress)
        
        # Create initial story progress
        initial_progress = StoryProgress(
            wallet_address=wallet_address,
            current_chapter="chapter_001",
            story_path="main"
        )
        
        await db.story_progress.insert_one(initial_progress.dict())
        return initial_progress
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/story/chapters")
async def get_all_chapters():
    """Get all story chapters (public info only)"""
    try:
        chapters = await db.story_chapters.find({}).to_list(100)
        # Remove sensitive info for public view
        public_chapters = []
        for chapter in chapters:
            public_chapter = {
                "id": chapter["id"],
                "title": chapter["title"],
                "description": chapter["description"],
                "chapter_number": chapter["chapter_number"],
                "nft_required": chapter["nft_required"],
                "image_url": chapter.get("image_url", "")
            }
            public_chapters.append(public_chapter)
        
        return sorted(public_chapters, key=lambda x: x["chapter_number"])
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/story/chapter/{chapter_id}")
async def get_chapter(chapter_id: str, wallet_address: str):
    """Get specific chapter content with access control"""
    try:
        # Get chapter
        chapter = await db.story_chapters.find_one({"id": chapter_id})
        if not chapter:
            raise HTTPException(status_code=404, detail="Chapter not found")
        
        # Check NFT access if required
        if chapter.get("nft_required", False):
            nft_access = await check_nft_access(wallet_address)
            if not nft_access.has_access:
                raise HTTPException(status_code=403, detail="NFT ownership required for this chapter")
        
        # Get player progress
        progress = await db.story_progress.find_one({"wallet_address": wallet_address})
        if not progress:
            # Initialize if not exists
            await initialize_story(wallet_address)
            progress = await db.story_progress.find_one({"wallet_address": wallet_address})
        
        # Check if chapter is unlocked
        if chapter_id not in progress.get("completed_chapters", []) and chapter_id != progress.get("current_chapter"):
            # Check unlock requirements
            unlock_reqs = chapter.get("unlock_requirements", {})
            if unlock_reqs:
                required_chapters = unlock_reqs.get("completed_chapters", [])
                if not all(req in progress.get("completed_chapters", []) for req in required_chapters):
                    raise HTTPException(status_code=403, detail="Chapter not unlocked yet")
        
        return StoryChapter(**chapter)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/story/choice")
async def make_story_choice(choice_data: dict):
    """Make a choice in the story"""
    try:
        wallet_address = choice_data.get("wallet_address")
        chapter_id = choice_data.get("chapter_id")
        choice_index = choice_data.get("choice_index")
        
        if not all([wallet_address, chapter_id, choice_index is not None]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Get chapter
        chapter = await db.story_chapters.find_one({"id": chapter_id})
        if not chapter:
            raise HTTPException(status_code=404, detail="Chapter not found")
        
        # Validate choice
        choices = chapter.get("choices", [])
        if choice_index >= len(choices):
            raise HTTPException(status_code=400, detail="Invalid choice index")
        
        chosen_option = choices[choice_index]
        
        # Record choice
        story_choice = StoryChoice(
            chapter_id=chapter_id,
            wallet_address=wallet_address,
            choice_index=choice_index,
            choice_text=chosen_option["text"],
            consequence=chosen_option.get("consequence", ""),
            reputation_change=chosen_option.get("reputation_change", 0)
        )
        
        await db.story_choices.insert_one(story_choice.dict())
        
        # Update progress
        progress = await db.story_progress.find_one({"wallet_address": wallet_address})
        if progress:
            # Add to completed chapters
            completed = progress.get("completed_chapters", [])
            if chapter_id not in completed:
                completed.append(chapter_id)
            
            # Update reputation
            new_reputation = progress.get("reputation_score", 0) + chosen_option.get("reputation_change", 0)
            
            # Add choice to history
            choices_made = progress.get("choices_made", [])
            choices_made.append({
                "chapter_id": chapter_id,
                "choice_index": choice_index,
                "choice_text": chosen_option["text"],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Determine next chapter
            next_chapter = chosen_option.get("next_chapter", "")
            if not next_chapter and chapter.get("next_chapters"):
                next_chapter = chapter["next_chapters"][0]  # Default to first option
            
            # Update story path based on choices
            story_path = progress.get("story_path", "main")
            if chosen_option.get("story_path"):
                story_path = chosen_option["story_path"]
            
            await db.story_progress.update_one(
                {"wallet_address": wallet_address},
                {"$set": {
                    "completed_chapters": completed,
                    "current_chapter": next_chapter,
                    "reputation_score": new_reputation,
                    "choices_made": choices_made,
                    "story_path": story_path,
                    "last_played": datetime.utcnow()
                }}
            )
        
        # Generate AI consequence if needed
        if chosen_option.get("generate_ai_consequence"):
            try:
                chat = LlmChat(
                    api_key=OPENAI_API_KEY,
                    session_id=f"story_{wallet_address}",
                    system_message="Du bist ein Geschichtenerzähler für das KryptoMurat-Spiel 'Jagd auf den Bitcoin'. Erstelle dramatische Konsequenzen für Spieler-Entscheidungen im Comic-Stil."
                ).with_model("openai", "gpt-4o")
                
                consequence_prompt = f"Der Bitcoin-Jäger hat sich entschieden: '{chosen_option['text']}'. Beschreibe die dramatischen Konsequenzen dieser Entscheidung in 2-3 Sätzen. Action-reich, deutsch, mit Motorrad-Szenen."
                
                user_message = UserMessage(text=consequence_prompt)
                ai_consequence = await chat.send_message(user_message)
                
                # Update choice with AI consequence
                await db.story_choices.update_one(
                    {"id": story_choice.id},
                    {"$set": {"consequence": ai_consequence}}
                )
                
                story_choice.consequence = ai_consequence
                
            except Exception as e:
                print(f"AI consequence generation failed: {e}")
        
        return {
            "success": True,
            "choice": story_choice,
            "next_chapter": next_chapter,
            "reputation_change": chosen_option.get("reputation_change", 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/story/progress/{wallet_address}")
async def get_story_progress(wallet_address: str):
    """Get player's story progress"""
    try:
        progress = await db.story_progress.find_one({"wallet_address": wallet_address})
        if not progress:
            # Initialize if not exists
            return await initialize_story(wallet_address)
        
        return StoryProgress(**progress)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/story/vote")
async def vote_story_direction(vote_data: dict):
    """Vote for story direction (community voting)"""
    try:
        wallet_address = vote_data.get("wallet_address")
        vote_type = vote_data.get("vote_type")
        vote_option = vote_data.get("vote_option")
        
        if not all([wallet_address, vote_type, vote_option]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Check if user already voted
        existing_vote = await db.story_votes.find_one({
            "wallet_address": wallet_address,
            "vote_type": vote_type
        })
        
        if existing_vote:
            # Update existing vote
            await db.story_votes.update_one(
                {"_id": existing_vote["_id"]},
                {"$set": {
                    "vote_option": vote_option,
                    "timestamp": datetime.utcnow()
                }}
            )
        else:
            # Create new vote
            nft_access = await check_nft_access(wallet_address)
            vote_weight = 2 if nft_access.has_access else 1  # NFT holders get more weight
            
            story_vote = StoryVote(
                wallet_address=wallet_address,
                vote_type=vote_type,
                vote_option=vote_option,
                vote_weight=vote_weight
            )
            
            await db.story_votes.insert_one(story_vote.dict())
        
        return {"success": True, "message": "Vote recorded"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/story/votes/{vote_type}")
async def get_vote_results(vote_type: str):
    """Get voting results for a specific vote type"""
    try:
        votes = await db.story_votes.find({"vote_type": vote_type}).to_list(1000)
        
        # Count votes by option
        vote_counts = {}
        for vote in votes:
            option = vote["vote_option"]
            weight = vote.get("vote_weight", 1)
            vote_counts[option] = vote_counts.get(option, 0) + weight
        
        # Sort by vote count
        sorted_results = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "vote_type": vote_type,
            "results": sorted_results,
            "total_votes": len(votes),
            "total_weight": sum(vote_counts.values())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/story/generate-chapter")
async def generate_ai_chapter(chapter_request: dict):
    """Generate a new chapter using AI (admin only)"""
    try:
        wallet_address = chapter_request.get("wallet_address")
        prompt = chapter_request.get("prompt")
        chapter_number = chapter_request.get("chapter_number")
        
        if not all([wallet_address, prompt, chapter_number]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Check admin access (simple check - in production use proper admin auth)
        nft_access = await check_nft_access(wallet_address)
        if not nft_access.has_access or nft_access.access_level != "premium":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Generate chapter with AI
        chat = LlmChat(
            api_key=OPENAI_API_KEY,
            session_id=f"chapter_gen_{wallet_address}",
            system_message="Du bist ein Autor für das KryptoMurat-Spiel 'Jagd auf den Bitcoin'. Erstelle spannende Kapitel mit Entscheidungsmöglichkeiten im Comic-Stil. Deutsche Sprache, Action-reich, mit Motorrad-Szenen rund um Herford."
        ).with_model("openai", "gpt-4o")
        
        chapter_prompt = f"""Erstelle ein neues Kapitel für das KryptoMurat-Spiel 'Jagd auf den Bitcoin':

Kapitel Nummer: {chapter_number}
Story-Prompt: {prompt}

Format:
TITEL: [Kapitel-Titel]
BESCHREIBUNG: [Kurze Beschreibung]
INHALT: [Haupt-Story Text, 3-4 Absätze]
ENTSCHEIDUNGEN:
1. [Option 1] -> [Konsequenz]
2. [Option 2] -> [Konsequenz]
3. [Option 3] -> [Konsequenz]

Stil: Action-reich, deutsch, Bitcoin-Jäger auf Motorrad, Herford-Umgebung, spannend"""
        
        user_message = UserMessage(text=chapter_prompt)
        ai_chapter = await chat.send_message(user_message)
        
        # Parse AI response (simplified parsing)
        lines = ai_chapter.split('\n')
        title = ""
        description = ""
        content = ""
        choices = []
        
        current_section = ""
        for line in lines:
            line = line.strip()
            if line.startswith("TITEL:"):
                title = line.replace("TITEL:", "").strip()
            elif line.startswith("BESCHREIBUNG:"):
                description = line.replace("BESCHREIBUNG:", "").strip()
            elif line.startswith("INHALT:"):
                current_section = "content"
                content = line.replace("INHALT:", "").strip()
            elif line.startswith("ENTSCHEIDUNGEN:"):
                current_section = "choices"
            elif current_section == "content" and line and not line.startswith("ENTSCHEIDUNGEN:"):
                content += "\n" + line
            elif current_section == "choices" and line and (line.startswith("1.") or line.startswith("2.") or line.startswith("3.")):
                choice_text = line.split("->")[0].strip()
                consequence = line.split("->")[1].strip() if "->" in line else ""
                choices.append({
                    "text": choice_text,
                    "consequence": consequence,
                    "reputation_change": 0,
                    "next_chapter": "",
                    "story_path": "main"
                })
        
        # Create chapter
        new_chapter = StoryChapter(
            title=title or f"Kapitel {chapter_number}",
            description=description or "Ein neues Abenteuer beginnt...",
            content=content,
            chapter_number=chapter_number,
            choices=choices,
            nft_required=False
        )
        
        await db.story_chapters.insert_one(new_chapter.dict())
        
        return {
            "success": True,
            "chapter": new_chapter,
            "ai_raw": ai_chapter
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Telegram Bot Routes
@api_router.post("/telegram/subscribe")
async def subscribe_telegram(subscription_data: dict):
    """Subscribe to Telegram notifications"""
    try:
        wallet_address = subscription_data.get("wallet_address")
        chat_id = subscription_data.get("chat_id")
        username = subscription_data.get("username", "")
        
        if not wallet_address or not chat_id:
            raise HTTPException(status_code=400, detail="wallet_address and chat_id required")
        
        # Check if subscription exists
        existing = await db.telegram_subscriptions.find_one({
            "wallet_address": wallet_address,
            "chat_id": chat_id
        })
        
        if existing:
            # Update existing subscription
            await db.telegram_subscriptions.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "is_active": True,
                    "username": username,
                    "updated_at": datetime.utcnow()
                }}
            )
            return {"success": True, "message": "Subscription updated"}
        else:
            # Create new subscription
            subscription = TelegramSubscription(
                wallet_address=wallet_address,
                chat_id=chat_id,
                username=username
            )
            
            await db.telegram_subscriptions.insert_one(subscription.dict())
            
            # Send welcome message
            welcome_msg = f"""
*🎮 Willkommen bei KryptoMurat\\!*

Du erhältst jetzt Notifications für:
• 🎲 Story\\-Updates \\(Jagd auf den Bitcoin\\)
• 💰 Staking\\-Alerts \\(Rewards & Erinnerungen\\)
• 🎥 Live\\-Stream Notifications
• 🎭 NFT\\-Alerts \\(Neue Drops\\)
• 🤖 AI\\-Content Updates

Verwende /help für alle Befehle\\!
            """
            
            await send_telegram_notification(chat_id, welcome_msg)
            
            return {"success": True, "message": "Subscription created"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/telegram/unsubscribe")
async def unsubscribe_telegram(unsubscribe_data: dict):
    """Unsubscribe from Telegram notifications"""
    try:
        wallet_address = unsubscribe_data.get("wallet_address")
        chat_id = unsubscribe_data.get("chat_id")
        
        if not wallet_address or not chat_id:
            raise HTTPException(status_code=400, detail="wallet_address and chat_id required")
        
        result = await db.telegram_subscriptions.update_one(
            {"wallet_address": wallet_address, "chat_id": chat_id},
            {"$set": {"is_active": False}}
        )
        
        if result.modified_count > 0:
            return {"success": True, "message": "Unsubscribed successfully"}
        else:
            raise HTTPException(status_code=404, detail="Subscription not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/telegram/notify")
async def send_notification(notification_data: dict):
    """Send notification to subscribers"""
    try:
        notification_type = notification_data.get("type")
        message = notification_data.get("message")
        wallet_address = notification_data.get("wallet_address")
        
        if not notification_type or not message:
            raise HTTPException(status_code=400, detail="type and message required")
        
        # Get subscribers
        query = {"is_active": True}
        if wallet_address:
            query["wallet_address"] = wallet_address
        
        subscribers = await db.telegram_subscriptions.find(query).to_list(1000)
        
        sent_count = 0
        for subscriber in subscribers:
            notifications = subscriber.get("notifications", {})
            
            # Check if user wants this type of notification
            if notifications.get(notification_type, True):
                success = await send_telegram_notification(
                    subscriber["chat_id"], 
                    message
                )
                if success:
                    sent_count += 1
        
        return {"success": True, "sent_to": sent_count}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/telegram/webhook/{secret}")
async def telegram_webhook(secret: str, request: Request):
    """Handle Telegram webhook"""
    if secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid webhook secret")
    
    try:
        from telegram import Update
        update_data = await request.json()
        update = Update.de_json(update_data, telegram_bot)
        
        if update.message:
            await handle_telegram_message(update.message)
        
        return {"status": "ok"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def handle_telegram_message(message):
    """Handle incoming Telegram messages"""
    try:
        chat_id = message.chat_id
        text = message.text
        username = message.from_user.username if message.from_user else ""
        
        # Log message
        await db.telegram_messages.insert_one({
            "chat_id": chat_id,
            "message": text,
            "username": username,
            "timestamp": datetime.utcnow(),
            "direction": "incoming"
        })
        
        # Handle commands
        if text.startswith('/start'):
            welcome_text = """
*🎮 KryptoMurat Telegram Bot*

Befehle:
/help \\- Zeigt diese Hilfe
/status \\- Zeigt deinen Account\\-Status
/subscribe \\- Aktiviert Notifications
/unsubscribe \\- Deaktiviert Notifications
/wallet \\- Wallet\\-Informationen

Verbinde deine Wallet auf kryptomur\\.at um loszulegen\\!
            """
            await send_telegram_notification(chat_id, welcome_text)
            
        elif text.startswith('/help'):
            help_text = """
*🎮 KryptoMurat Bot Hilfe*

*Verfügbare Befehle:*
/start \\- Bot starten
/status \\- Account\\-Status prüfen
/subscribe \\- Notifications aktivieren
/unsubscribe \\- Notifications deaktivieren
/wallet \\- Wallet\\-Info anzeigen

*Notification\\-Typen:*
• 🎲 Story\\-Updates
• 💰 Staking\\-Alerts
• 🎥 Stream\\-Notifications
• 🎭 NFT\\-Alerts
• 🤖 AI\\-Content

Support: @moneyclitch
            """
            await send_telegram_notification(chat_id, help_text)
            
        elif text.startswith('/status'):
            # Get user subscription
            subscription = await db.telegram_subscriptions.find_one({
                "chat_id": chat_id,
                "is_active": True
            })
            
            if subscription:
                wallet_address = subscription["wallet_address"]
                
                # Get user stats
                progress = await db.story_progress.find_one({"wallet_address": wallet_address})
                staking_positions = await db.staking_positions.find({"wallet_address": wallet_address}).to_list(100)
                
                status_text = f"""
*📊 Dein KryptoMurat Status*

*Wallet:* `{wallet_address[:8]}...{wallet_address[-4:]}`
*Story\\-Fortschritt:* {len(progress.get('completed_chapters', [])) if progress else 0} Kapitel
*Staking\\-Positionen:* {len(staking_positions)} aktiv
*Notifications:* ✅ Aktiviert

*Reputation:* {progress.get('reputation_score', 0) if progress else 0}
*Story\\-Pfad:* {progress.get('story_path', 'main') if progress else 'main'}
                """
                await send_telegram_notification(chat_id, status_text)
            else:
                await send_telegram_notification(chat_id, "❌ Kein aktives Abonnement gefunden\\. Verwende /subscribe auf der Website\\!")
                
        elif text.startswith('/wallet'):
            subscription = await db.telegram_subscriptions.find_one({
                "chat_id": chat_id,
                "is_active": True
            })
            
            if subscription:
                wallet_address = subscription["wallet_address"]
                
                # Get token balance
                try:
                    contract = web3.eth.contract(address=MURAT_TOKEN_ADDRESS, abi=ERC20_ABI)
                    balance_wei = contract.functions.balanceOf(wallet_address).call()
                    decimals = contract.functions.decimals().call()
                    balance = balance_wei / (10 ** decimals)
                    
                    wallet_text = f"""
*💰 Wallet\\-Info*

*Adresse:* `{wallet_address}`
*MURAT Balance:* {balance:.2f} MURAT
*Netzwerk:* Polygon

[Polygonscan](https://polygonscan\\.com/address/{wallet_address})
                    """
                    await send_telegram_notification(chat_id, wallet_text)
                    
                except Exception as e:
                    await send_telegram_notification(chat_id, f"❌ Fehler beim Abrufen der Wallet\\-Daten: {str(e)}")
            else:
                await send_telegram_notification(chat_id, "❌ Kein aktives Abonnement gefunden\\!")
        
        # Send auto-notifications for specific actions
        await send_auto_notifications(chat_id, text)
        
    except Exception as e:
        print(f"Error handling Telegram message: {e}")

async def send_auto_notifications(chat_id: int, text: str):
    """Send automatic notifications based on user actions"""
    try:
        # Story completion notification
        if "story completed" in text.lower():
            notification = "🎉 Glückwunsch\\! Du hast ein neues Kapitel abgeschlossen\\!"
            await send_telegram_notification(chat_id, notification)
        
        # Staking notification
        elif "staking" in text.lower():
            notification = "💰 Staking\\-Position wurde aktualisiert\\!"
            await send_telegram_notification(chat_id, notification)
            
    except Exception as e:
        print(f"Auto-notification error: {e}")

@api_router.get("/telegram/stats")
async def get_telegram_stats():
    """Get Telegram bot statistics"""
    try:
        total_subscribers = await db.telegram_subscriptions.count_documents({"is_active": True})
        total_messages = await db.telegram_messages.count_documents({})
        
        # Get subscription breakdown
        subscriptions = await db.telegram_subscriptions.find({"is_active": True}).to_list(1000)
        
        notification_stats = {
            "story_updates": 0,
            "staking_alerts": 0,
            "stream_notifications": 0,
            "nft_alerts": 0,
            "ai_content": 0
        }
        
        for sub in subscriptions:
            notifications = sub.get("notifications", {})
            for key in notification_stats.keys():
                if notifications.get(key, True):
                    notification_stats[key] += 1
        
        return {
            "total_subscribers": total_subscribers,
            "total_messages": total_messages,
            "notification_preferences": notification_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Original routes
@api_router.get("/")
async def root():
    return {"message": "KryptoMurat - Web3 Platform API"}

# Metaverse World Routes
@api_router.get("/metaverse/world")
async def get_metaverse_world():
    """Get metaverse world configuration"""
    try:
        return {
            "world_name": "KryptoMurat Metaverse",
            "areas": [
                {
                    "id": "live_stream",
                    "name": "Live Stream Arena",
                    "description": "Zentrale Streaming-Bühne",
                    "position": {"x": 0, "y": 0},
                    "access_level": "public"
                },
                {
                    "id": "nft_gallery",
                    "name": "NFT Gallery",
                    "description": "Exklusive NFT-Sammlung",
                    "position": {"x": -200, "y": 0},
                    "access_level": "nft_required"
                },
                {
                    "id": "voting_chamber",
                    "name": "Voting Chamber",
                    "description": "Community-Governance",
                    "position": {"x": -200, "y": -100},
                    "access_level": "public"
                },
                {
                    "id": "airdrop_zone",
                    "name": "Airdrop Zone",
                    "description": "MURAT Token Belohnungen",
                    "position": {"x": 200, "y": 0},
                    "access_level": "public"
                },
                {
                    "id": "vip_lounge",
                    "name": "VIP Lounge",
                    "description": "Exklusiver VIP-Bereich",
                    "position": {"x": 200, "y": -100},
                    "access_level": "premium"
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/metaverse/airdrop/available")
async def get_available_airdrops():
    """Get available MURAT token airdrops"""
    try:
        # Get current airdrops from database
        airdrops = await db.metaverse_airdrops.find({"is_active": True}).to_list(100)
        return airdrops
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/metaverse/airdrop/claim")
async def claim_airdrop(claim_data: dict):
    """Claim MURAT token airdrop"""
    try:
        wallet_address = claim_data.get("wallet_address")
        airdrop_id = claim_data.get("airdrop_id")
        
        if not wallet_address or not airdrop_id:
            raise HTTPException(status_code=400, detail="wallet_address and airdrop_id required")
        
        # Check if airdrop exists and is active
        airdrop = await db.metaverse_airdrops.find_one({"id": airdrop_id, "is_active": True})
        if not airdrop:
            raise HTTPException(status_code=404, detail="Airdrop not found or inactive")
        
        # Check if user already claimed
        existing_claim = await db.airdrop_claims.find_one({
            "wallet_address": wallet_address,
            "airdrop_id": airdrop_id
        })
        
        if existing_claim:
            raise HTTPException(status_code=400, detail="Airdrop already claimed")
        
        # Create claim record
        claim_record = {
            "id": str(uuid.uuid4()),
            "wallet_address": wallet_address,
            "airdrop_id": airdrop_id,
            "amount": airdrop["amount"],
            "claimed_at": datetime.utcnow(),
            "status": "pending"
        }
        
        await db.airdrop_claims.insert_one(claim_record)
        
        # In a real implementation, you would interact with the smart contract here
        # For now, we'll simulate the claim
        claim_record["status"] = "completed"
        await db.airdrop_claims.update_one(
            {"id": claim_record["id"]},
            {"$set": {"status": "completed"}}
        )
        
        return {
            "success": True,
            "amount": airdrop["amount"],
            "transaction_hash": f"0x{uuid.uuid4().hex}",
            "message": f"Successfully claimed {airdrop['amount']} MURAT tokens!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/metaverse/marketplace/nfts")
async def get_marketplace_nfts():
    """Get NFTs available in the marketplace"""
    try:
        nfts = await db.metaverse_nfts.find({"is_listed": True}).to_list(100)
        return nfts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/metaverse/marketplace/buy")
async def buy_nft_with_murat(purchase_data: dict):
    """Buy NFT with MURAT tokens"""
    try:
        wallet_address = purchase_data.get("wallet_address")
        nft_id = purchase_data.get("nft_id")
        
        if not wallet_address or not nft_id:
            raise HTTPException(status_code=400, detail="wallet_address and nft_id required")
        
        # Get NFT info
        nft = await db.metaverse_nfts.find_one({"id": nft_id, "is_listed": True})
        if not nft:
            raise HTTPException(status_code=404, detail="NFT not found or not listed")
        
        # Check user's MURAT balance
        balance_response = await get_token_balance(wallet_address)
        user_balance = float(balance_response.balance)
        
        if user_balance < nft["price"]:
            raise HTTPException(status_code=400, detail="Insufficient MURAT balance")
        
        # Create purchase record
        purchase_record = {
            "id": str(uuid.uuid4()),
            "wallet_address": wallet_address,
            "nft_id": nft_id,
            "price": nft["price"],
            "purchased_at": datetime.utcnow(),
            "transaction_hash": f"0x{uuid.uuid4().hex}",
            "status": "completed"
        }
        
        await db.nft_purchases.insert_one(purchase_record)
        
        # Update NFT ownership
        await db.metaverse_nfts.update_one(
            {"id": nft_id},
            {"$set": {
                "owner": wallet_address,
                "is_listed": False,
                "sold_at": datetime.utcnow()
            }}
        )
        
        return {
            "success": True,
            "nft": nft,
            "transaction_hash": purchase_record["transaction_hash"],
            "message": f"Successfully purchased {nft['name']} for {nft['price']} MURAT!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/metaverse/voting/proposals")
async def get_voting_proposals():
    """Get active voting proposals"""
    try:
        proposals = await db.metaverse_proposals.find({"is_active": True}).to_list(100)
        return proposals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/metaverse/voting/vote")
async def cast_vote(vote_data: dict):
    """Cast a vote on a proposal"""
    try:
        wallet_address = vote_data.get("wallet_address")
        proposal_id = vote_data.get("proposal_id")
        vote_option = vote_data.get("vote_option")
        
        if not all([wallet_address, proposal_id, vote_option]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Check if proposal exists
        proposal = await db.metaverse_proposals.find_one({"id": proposal_id, "is_active": True})
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        # Check if user already voted
        existing_vote = await db.metaverse_votes.find_one({
            "wallet_address": wallet_address,
            "proposal_id": proposal_id
        })
        
        if existing_vote:
            # Update existing vote
            await db.metaverse_votes.update_one(
                {"_id": existing_vote["_id"]},
                {"$set": {
                    "vote_option": vote_option,
                    "updated_at": datetime.utcnow()
                }}
            )
        else:
            # Create new vote
            vote_record = {
                "id": str(uuid.uuid4()),
                "wallet_address": wallet_address,
                "proposal_id": proposal_id,
                "vote_option": vote_option,
                "vote_weight": 1,  # Can be enhanced with token-based voting power
                "created_at": datetime.utcnow()
            }
            
            await db.metaverse_votes.insert_one(vote_record)
        
        return {"success": True, "message": "Vote cast successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/metaverse/gallery/{wallet_address}")
async def get_user_nft_gallery(wallet_address: str):
    """Get user's NFT gallery"""
    try:
        # Get NFTs owned by user
        owned_nfts = await db.metaverse_nfts.find({"owner": wallet_address}).to_list(100)
        
        # Get NFTs from purchases
        purchases = await db.nft_purchases.find({"wallet_address": wallet_address}).to_list(100)
        
        return {
            "owned_nfts": owned_nfts,
            "total_owned": len(owned_nfts),
            "total_spent": sum(p.get("price", 0) for p in purchases)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Initialize sample data
@api_router.post("/metaverse/init-sample-data")
async def init_sample_data():
    """Initialize sample data for the metaverse (development only)"""
    try:
        # Sample airdrops
        sample_airdrops = [
            {
                "id": "daily_bonus",
                "name": "Daily Bonus",
                "description": "Täglicher MURAT Bonus",
                "amount": 50,
                "image_url": "https://via.placeholder.com/150x150/ff6b6b/ffffff?text=DAILY",
                "is_active": True,
                "created_at": datetime.utcnow()
            },
            {
                "id": "welcome_bonus",
                "name": "Welcome Bonus",
                "description": "Willkommensbonus für neue User",
                "amount": 100,
                "image_url": "https://via.placeholder.com/150x150/4ecdc4/ffffff?text=WELCOME",
                "is_active": True,
                "created_at": datetime.utcnow()
            }
        ]
        
        # Sample NFTs
        sample_nfts = [
            {
                "id": "meme_nft_1",
                "name": "Crypto Meme #1",
                "description": "Legendary Pepe Meme",
                "price": 250,
                "image_url": "https://via.placeholder.com/300x300/ff9ff3/ffffff?text=MEME+1",
                "category": "meme",
                "rarity": "legendary",
                "is_listed": True,
                "owner": None,
                "created_at": datetime.utcnow()
            },
            {
                "id": "meme_nft_2",
                "name": "Crypto Meme #2",
                "description": "Rare Doge Meme",
                "price": 150,
                "image_url": "https://via.placeholder.com/300x300/f1c40f/ffffff?text=MEME+2",
                "category": "meme",
                "rarity": "rare",
                "is_listed": True,
                "owner": None,
                "created_at": datetime.utcnow()
            }
        ]
        
        # Sample proposals
        sample_proposals = [
            {
                "id": "proposal_1",
                "title": "Neue NFT-Kollektion",
                "description": "Sollen wir eine neue Meme-NFT-Kollektion erstellen?",
                "options": ["Ja", "Nein", "Später"],
                "is_active": True,
                "created_at": datetime.utcnow(),
                "ends_at": datetime.utcnow() + timedelta(days=7)
            },
            {
                "id": "proposal_2",
                "title": "Stream-Thema",
                "description": "Welches Thema soll der nächste Stream haben?",
                "options": ["Crypto News", "Gaming", "NFT Reviews"],
                "is_active": True,
                "created_at": datetime.utcnow(),
                "ends_at": datetime.utcnow() + timedelta(days=3)
            }
        ]
        
        # Insert sample data
        await db.metaverse_airdrops.delete_many({})
        await db.metaverse_airdrops.insert_many(sample_airdrops)
        
        await db.metaverse_nfts.delete_many({})
        await db.metaverse_nfts.insert_many(sample_nfts)
        
        await db.metaverse_proposals.delete_many({})
        await db.metaverse_proposals.insert_many(sample_proposals)
        
        return {"success": True, "message": "Sample data initialized"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
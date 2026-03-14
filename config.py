"""
Configuration settings for the Auction Management System.

This module contains all configuration constants and settings.
League-specific settings (name, season) are loaded from data/settings.json.
"""

import json
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
IMAGES_DIR = BASE_DIR / "images"

# File paths
PLAYERS_CSV_PATH = DATA_DIR / "player.csv"
TEAMS_CONFIG_PATH = DATA_DIR / "config.json"
PLAYER_ORDER_EXCEPTIONS_PATH = DATA_DIR / "player_order_exceptions.json"
SETTINGS_PATH = DATA_DIR / "settings.json"

# Load league settings
def _load_settings() -> dict:
    if SETTINGS_PATH.exists():
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

_settings = _load_settings()

LEAGUE_NAME: str = _settings.get("league_name", "Cricket Auction")
LEAGUE_SEASON: str = _settings.get("season", "")
_connection_question: str = _settings.get("connection_question", "What is your connection to the league?")

# CSV column mappings
CSV_COLUMNS = {
    "timestamp": "Timestamp",
    "full_name": "Full Name",
    "contact_number": "Contact Number (WhatsApp preferred)",
    "batting_hand": "Select your batting hand and bowling arm [Batting Hand]",
    "bowling_hand": "Select your batting hand and bowling arm [Bowling Hand]",
    "primary_role": "What is your primary role on the pitch?",
    "connection": _connection_question,
}

# Default team configuration
DEFAULT_TEAMS = [
    {"name": "Team A", "owner": "Owner A", "budget": 100000},
    {"name": "Team B", "owner": "Owner B", "budget": 100000},
    {"name": "Team C", "owner": "Owner C", "budget": 100000},
    {"name": "Team D", "owner": "Owner D", "budget": 100000},
]

# Auction settings
MIN_BID_AMOUNT = 500  # Minimum bid amount for all players
DEFAULT_BID_INCREMENT = 500
UNSOLD_THRESHOLD = 0  # Price below which player goes unsold
REQUIRED_PLAYERS_PER_TEAM = 14  # Each team must have exactly 14 players (1 owner + 13 auctioned players)
BUDGET_RECOVERY_PERCENTAGE = 0.5  # 50% refund when selling back highest bid player
ANIMATION_PLAYER_COUNT = 10  # Number of players to show in random selection animation
ANIMATION_DURATION = 3  # Duration of animation in seconds

# UI Settings
SIDEBAR_WIDTH = 300
IMAGE_WIDTH = 300  # Reduced for better screen fit
DEFAULT_PLAYER_IMAGE = "default_player.png"

# Styling
TEAM_COLORS = [
    "#FF6B6B",  # Red
    "#4ECDC4",  # Teal
    "#45B7D1",  # Blue
    "#FFA07A",  # Light Salmon
    "#98D8C8",  # Mint
    "#F7DC6F",  # Yellow
    "#BB8FCE",  # Purple
    "#85C1E2",  # Sky Blue
]

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True)

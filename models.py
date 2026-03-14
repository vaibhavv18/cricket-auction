"""Data models for players, teams, and auction state."""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class PlayerRole(Enum):
    """Enumeration of player roles."""

    BATSMAN = "Batsman"
    BOWLER = "Bowler"
    WICKET_KEEPER = "Wicket-Keeper"
    ALL_ROUNDER_PACE = "All-Rounder (Pace Focus)"
    ALL_ROUNDER_SPIN = "All-Rounder (Spin Focus)"


class BattingHand(Enum):
    """Enumeration of batting hand types."""

    RIGHT = "Right"
    LEFT = "Left"


class BowlingHand(Enum):
    """Enumeration of bowling hand types."""

    RIGHT = "Right"
    LEFT = "Left"


class Connection(Enum):
    """Enumeration of connection to Halar."""

    LOCAL = "Local (from within the Village)"
    OUTSIDER = "Outsider (from outside the Village)"


@dataclass
class Player:
    """Represents a cricket player in the auction."""

    full_name: str
    contact_number: str
    batting_hand: str
    bowling_hand: str
    primary_role: str
    connection: str
    photo_filename: Optional[str] = None
    timestamp: Optional[str] = None
    is_sold: bool = False
    sold_to: Optional[str] = None
    sold_price: int = 0

    def __post_init__(self):
        """Validate and process player data after initialization."""
        if not self.full_name or not self.full_name.strip():
            raise ValueError("Player name cannot be empty")

        if not self.contact_number or not self.contact_number.strip():
            raise ValueError("Contact number cannot be empty")

    def mark_sold(self, team_name: str, price: int) -> None:
        """
        Mark the player as sold to a team.

        Args:
            team_name: Name of the team that bought the player
            price: Price at which the player was sold
        """
        self.is_sold = True
        self.sold_to = team_name
        self.sold_price = price

    def mark_unsold(self) -> None:
        """Mark the player as unsold."""
        self.is_sold = False
        self.sold_to = None
        self.sold_price = 0


@dataclass
class Team:
    """Represents a team in the auction."""

    name: str
    owner: str
    initial_budget: int
    remaining_budget: int
    logo_filename: Optional[str] = None
    players: list[Player] = field(default_factory=list)

    def __post_init__(self):
        """Validate team data after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError("Team name cannot be empty")

        if not self.owner or not self.owner.strip():
            raise ValueError("Owner name cannot be empty")

        if self.initial_budget <= 0:
            raise ValueError("Initial budget must be positive")

        if self.remaining_budget < 0:
            raise ValueError("Remaining budget cannot be negative")

    def add_player(self, player: Player, price: int) -> bool:
        """
        Add a player to the team if budget allows.

        Args:
            player: Player object to add
            price: Price to pay for the player

        Returns:
            True if player was added successfully, False otherwise
        """
        if price > self.remaining_budget:
            return False

        self.remaining_budget -= price
        player.mark_sold(self.name, price)
        self.players.append(player)
        return True

    def get_player_count(self) -> int:
        """Get the number of players in the team."""
        return len(self.players)

    def get_total_spent(self) -> int:
        """Calculate total amount spent on players."""
        return self.initial_budget - self.remaining_budget

    def remove_player(self, player: Player) -> bool:
        """
        Remove a player from the team.

        Args:
            player: Player object to remove

        Returns:
            True if player was removed successfully, False otherwise
        """
        if player in self.players:
            self.players.remove(player)
            return True
        return False

    def get_highest_bid_player(self) -> Optional[Player]:
        """
        Get the player with the highest bid in the team.

        Returns:
            Player object with highest bid, or None if team is empty
        """
        if not self.players:
            return None
        return max(self.players, key=lambda p: p.sold_price)


@dataclass
class AuctionState:
    """Represents the current state of the auction."""

    current_round: int = 1
    current_player: Optional[Player] = None
    remaining_players: list[Player] = field(default_factory=list)
    unsold_players: list[Player] = field(default_factory=list)
    auctioned_in_current_round: list[Player] = field(default_factory=list)
    is_auction_complete: bool = False
    required_players_per_team: int = 14

    def get_total_players_auctioned(self) -> int:
        """Get count of players that have been auctioned (sold or unsold)."""
        return len(self.remaining_players) == 0 and len(self.unsold_players) > 0

    def has_players_remaining(self) -> bool:
        """Check if there are players remaining to be auctioned."""
        return len(self.remaining_players) > 0 or len(self.unsold_players) > 0

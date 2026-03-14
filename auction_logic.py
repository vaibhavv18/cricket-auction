"""
Auction logic module for the Auction Management System.

Handles core auction functionality including player selection, bidding, and round management.
"""

import json
import logging
import random
from pathlib import Path
from typing import Optional

from config import PLAYER_ORDER_EXCEPTIONS_PATH
from models import AuctionState, Player, Team

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuctionManager:
    """Manages the auction process and state."""

    def __init__(self, players: list[Player], teams: list[Team]):
        """
        Initialize the AuctionManager.

        Args:
            players: List of all players in the auction
            teams: List of all teams participating
        """
        self.teams = teams
        self.all_players = players.copy()

        # Initialize auction state
        self.state = AuctionState(
            current_round=1,
            remaining_players=players.copy(),
            unsold_players=[],
        )

        # Apply player order exceptions and shuffle
        self._apply_player_order_exceptions()
        logger.info(
            f"Initialized auction with {len(players)} players and {len(teams)} teams"
        )

    def _load_player_order_exceptions(self) -> dict[str, int]:
        """
        Load player order exceptions from JSON file.

        Returns:
            Dictionary mapping player names to their desired positions
        """
        try:
            if not PLAYER_ORDER_EXCEPTIONS_PATH.exists():
                logger.info("No player order exceptions file found")
                return {}

            with open(PLAYER_ORDER_EXCEPTIONS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Filter out comment keys (starting with _)
            exceptions = {
                k: v for k, v in data.items() if not k.startswith("_")
            }

            if exceptions:
                logger.warning(
                    f"⚠️ PLAYER ORDER EXCEPTIONS ACTIVE: {len(exceptions)} players have fixed positions"
                )
                for player_name, position in exceptions.items():
                    logger.warning(f"   - {player_name} → Position {position}")

            return exceptions

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing player order exceptions: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading player order exceptions: {e}")
            return {}

    def _apply_player_order_exceptions(self) -> None:
        """
        Apply player order exceptions and shuffle remaining players.

        Players specified in exceptions will be placed at their designated positions.
        All other players will be randomly shuffled around them.
        """
        exceptions = self._load_player_order_exceptions()

        if not exceptions:
            # No exceptions, just shuffle normally
            random.shuffle(self.state.remaining_players)
            return

        # Create a mapping of player names to player objects
        player_map = {p.full_name: p for p in self.state.remaining_players}

        # Validate exceptions
        valid_exceptions = {}
        for player_name, position in exceptions.items():
            if player_name not in player_map:
                logger.warning(
                    f"Exception player '{player_name}' not found in player list"
                )
                continue

            # Convert to 0-based index
            index = position - 1

            if index < 0 or index >= len(self.state.remaining_players):
                logger.warning(
                    f"Invalid position {position} for '{player_name}' (valid: 1-{len(self.state.remaining_players)})"
                )
                continue

            valid_exceptions[player_name] = index

        if not valid_exceptions:
            random.shuffle(self.state.remaining_players)
            return

        # Separate exception players from others
        exception_players = {
            name: player_map[name] for name in valid_exceptions.keys()
        }
        other_players = [
            p for p in self.state.remaining_players
            if p.full_name not in exception_players
        ]

        # Shuffle the non-exception players
        random.shuffle(other_players)

        # Create final order with placeholders
        final_order = [None] * len(self.state.remaining_players)

        # Place exception players at their designated positions
        for player_name, index in valid_exceptions.items():
            final_order[index] = exception_players[player_name]

        # Fill remaining positions with shuffled players
        other_index = 0
        for i in range(len(final_order)):
            if final_order[i] is None:
                final_order[i] = other_players[other_index]
                other_index += 1

        self.state.remaining_players = final_order
        logger.info(
            f"Applied {len(valid_exceptions)} player order exceptions"
        )

    def get_next_player(self) -> Optional[Player]:
        """
        Get the next player for auction.

        Returns:
            Next Player object, or None if no players remaining
        """
        if self.state.remaining_players:
            self.state.current_player = self.state.remaining_players.pop(0)
            logger.info(f"Next player: {self.state.current_player.full_name}")
            return self.state.current_player

        # If no remaining players but unsold players exist, start next round
        if self.state.unsold_players:
            self._start_next_round()
            return self.get_next_player()

        # No players left
        self.state.is_auction_complete = True
        self.state.current_player = None
        logger.info("Auction complete - no players remaining")
        return None

    def _start_next_round(self) -> None:
        """Start the next round with unsold players."""
        self.state.current_round += 1
        self.state.remaining_players = self.state.unsold_players.copy()
        self.state.unsold_players = []

        # Clear auctioned players list for new round
        self.state.auctioned_in_current_round = []

        # Shuffle unsold players for random order
        random.shuffle(self.state.remaining_players)

        logger.info(
            f"Starting round {self.state.current_round} with "
            f"{len(self.state.remaining_players)} unsold players"
        )

    def sell_player(
        self, team_name: str, price: int, player: Optional[Player] = None
    ) -> tuple[bool, str]:
        """
        Sell a player to a team.

        Args:
            team_name: Name of the team buying the player
            price: Price to pay for the player
            player: Player object to sell. Uses current player if not provided.

        Returns:
            Tuple of (success: bool, message: str)
        """
        if player is None:
            player = self.state.current_player

        if player is None:
            return False, "No player currently being auctioned"

        # Find the team
        team = self._get_team_by_name(team_name)
        if team is None:
            return False, f"Team '{team_name}' not found"

        # Validate price
        if price <= 0:
            return False, "Price must be positive"

        # Check if team has sufficient budget
        if price > team.remaining_budget:
            return (
                False,
                f"Insufficient budget. {team.name} has "
                f"₹{team.remaining_budget:,} remaining",
            )

        # Add player to team
        success = team.add_player(player, price)
        if success:
            # Mark player as auctioned in current round
            self.mark_player_auctioned_in_round(player)

            logger.info(
                f"Sold {player.full_name} to {team.name} for ₹{price:,}"
            )
            return True, f"Sold to {team.name} for ₹{price:,}"
        else:
            return False, "Failed to add player to team"

    def mark_unsold(self, player: Optional[Player] = None) -> tuple[bool, str]:
        """
        Mark a player as unsold.

        Args:
            player: Player object to mark unsold. Uses current player if not provided.

        Returns:
            Tuple of (success: bool, message: str)
        """
        if player is None:
            player = self.state.current_player

        if player is None:
            return False, "No player currently being auctioned"

        player.mark_unsold()
        self.state.unsold_players.append(player)

        # Mark player as auctioned in current round
        self.mark_player_auctioned_in_round(player)

        logger.info(f"Marked {player.full_name} as unsold")
        return True, f"{player.full_name} marked as unsold"

    def _get_team_by_name(self, team_name: str) -> Optional[Team]:
        """
        Get a team by its name.

        Args:
            team_name: Name of the team to find

        Returns:
            Team object if found, None otherwise
        """
        for team in self.teams:
            if team.name == team_name:
                return team
        return None

    def get_auction_statistics(self) -> dict:
        """
        Get current auction statistics.

        Returns:
            Dictionary containing auction statistics
        """
        total_players = len(self.all_players)
        sold_players = sum(team.get_player_count() for team in self.teams)
        unsold_count = len(self.state.unsold_players)
        remaining_count = len(self.state.remaining_players)

        total_spent = sum(team.get_total_spent() for team in self.teams)

        return {
            "total_players": total_players,
            "sold_players": sold_players,
            "unsold_players": unsold_count,
            "remaining_players": remaining_count,
            "current_round": self.state.current_round,
            "total_spent": total_spent,
            "is_complete": self.state.is_auction_complete,
        }

    def reset_auction(self) -> None:
        """Reset the auction to initial state."""
        # Reset all teams but preserve owner (first player)
        for team in self.teams:
            team.remaining_budget = team.initial_budget
            # Keep only the owner (first player if they exist and are marked as owner)
            owner_players = [p for p in team.players if p.primary_role == "Team Owner"]
            team.players = owner_players

        # Reset all players
        for player in self.all_players:
            player.mark_unsold()

        # Reset state
        self.state = AuctionState(
            current_round=1,
            remaining_players=self.all_players.copy(),
            unsold_players=[],
        )

        # Apply player order exceptions and shuffle
        self._apply_player_order_exceptions()

        logger.info("Auction reset to initial state")

    def get_teams_summary(self) -> list[dict]:
        """
        Get summary information for all teams.

        Returns:
            List of dictionaries containing team summary data
        """
        summaries = []
        for team in self.teams:
            summaries.append(
                {
                    "name": team.name,
                    "owner": team.owner,
                    "remaining_budget": team.remaining_budget,
                    "total_spent": team.get_total_spent(),
                    "player_count": team.get_player_count(),
                    "players": team.players,
                }
            )
        return summaries

    def validate_team_completion(self, team: Team) -> tuple[bool, str]:
        """
        Validate if a team has the required number of players.

        Args:
            team: Team object to validate

        Returns:
            Tuple of (is_complete: bool, message: str)
        """
        required = self.state.required_players_per_team
        current = team.get_player_count()

        if current == required:
            return True, f"{team.name} has all {required} players"
        elif current < required:
            return False, f"{team.name} needs {required - current} more players"
        else:
            return False, f"{team.name} has too many players ({current}/{required})"

    def sellback_highest_player(self, team: Team) -> tuple[bool, str, Optional[Player]]:
        """
        Sell back the highest bid player from a team and return 50% budget.

        Args:
            team: Team object from which to sell back player

        Returns:
            Tuple of (success: bool, message: str, player: Optional[Player])
        """
        from config import BUDGET_RECOVERY_PERCENTAGE

        highest_player = team.get_highest_bid_player()

        if highest_player is None:
            return False, f"{team.name} has no players to sell back", None

        # Calculate refund (50% of sold price)
        refund_amount = int(highest_player.sold_price * BUDGET_RECOVERY_PERCENTAGE)

        # Remove player from team
        team.remove_player(highest_player)

        # Refund budget
        team.remaining_budget += refund_amount

        # Mark player as unsold and add to auction pool
        highest_player.mark_unsold()
        self.state.remaining_players.append(highest_player)

        message = (
            f"Sold back {highest_player.full_name} from {team.name}. "
            f"Refunded ₹{refund_amount:,} (50% of ₹{highest_player.sold_price:,})"
        )

        logger.info(message)
        return True, message, highest_player

    def check_team_budget_issues(self) -> list[dict]:
        """
        Check all teams for budget issues (can't afford minimum bid).

        Returns:
            List of teams with budget issues and suggested actions
        """
        from config import MIN_BID_AMOUNT

        issues = []

        for team in self.teams:
            players_needed = (
                self.state.required_players_per_team - team.get_player_count()
            )

            if players_needed > 0:
                # Check if team can afford minimum bid
                if team.remaining_budget < MIN_BID_AMOUNT:
                    highest_player = team.get_highest_bid_player()
                    if highest_player:
                        issues.append(
                            {
                                "team": team,
                                "players_needed": players_needed,
                                "budget": team.remaining_budget,
                                "highest_player": highest_player.full_name,
                                "highest_bid": highest_player.sold_price,
                                "refund_if_sold": int(
                                    highest_player.sold_price * 0.5
                                ),
                            }
                        )

        return issues

    def get_random_animation_pool(self) -> list[Player]:
        """
        Get a pool of players for random selection animation.

        Excludes players already auctioned in current round.

        Returns:
            List of players eligible for animation
        """
        from config import ANIMATION_PLAYER_COUNT

        # Get players who haven't been auctioned in current round
        eligible_players = [
            p
            for p in self.state.remaining_players
            if p not in self.state.auctioned_in_current_round
        ]

        # If not enough eligible players, use all remaining
        if len(eligible_players) < ANIMATION_PLAYER_COUNT:
            return eligible_players.copy()

        # Return random sample
        return random.sample(eligible_players, min(ANIMATION_PLAYER_COUNT, len(eligible_players)))

    def mark_player_auctioned_in_round(self, player: Player) -> None:
        """
        Mark a player as auctioned in the current round.

        Args:
            player: Player who was just auctioned
        """
        if player not in self.state.auctioned_in_current_round:
            self.state.auctioned_in_current_round.append(player)

    def skip_current_player(self) -> Optional[Player]:
        """
        Skip the current player and get the next one.

        This is useful for debugging or if a player needs to be skipped.

        Returns:
            Next Player object, or None if no players remaining
        """
        if self.state.current_player:
            logger.info(f"Skipping player: {self.state.current_player.full_name}")

        return self.get_next_player()

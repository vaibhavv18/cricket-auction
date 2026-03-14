"""Data management — loads players from CSV and handles auction result exports."""

import json
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from config import (
    CSV_COLUMNS,
    DATA_DIR,
    DEFAULT_TEAMS,
    PLAYERS_CSV_PATH,
    TEAMS_CONFIG_PATH,
)
from models import Player, Team

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataManager:
    """Manages data loading and persistence for the auction system."""

    def __init__(self):
        """Initialize the DataManager."""
        self.players: list[Player] = []
        self.teams: list[Team] = []

    def load_players_from_csv(self, csv_path: Optional[Path] = None, exclude_owners: list[str] = None) -> list[Player]:
        """
        Load players from CSV file.

        Args:
            csv_path: Path to the CSV file. Uses default if not provided.
            exclude_owners: List of owner names to exclude from auction

        Returns:
            List of Player objects

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV format is invalid
        """
        if exclude_owners is None:
            exclude_owners = []
        if csv_path is None:
            csv_path = PLAYERS_CSV_PATH

        if not csv_path.exists():
            raise FileNotFoundError(f"Players CSV not found at {csv_path}")

        try:
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded CSV with {len(df)} rows")

            # Validate required columns
            required_cols = CSV_COLUMNS
            missing_cols = set(required_cols.values()) - set(df.columns)
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            players = []
            for _, row in df.iterrows():
                try:
                    full_name = str(row[CSV_COLUMNS["full_name"]]).strip()

                    # Check if this player is an owner (fuzzy match)
                    is_owner = False
                    for owner_name in exclude_owners:
                        # Case-insensitive partial match
                        if owner_name.lower() in full_name.lower():
                            logger.info(f"Excluding owner from auction: {full_name}")
                            is_owner = True
                            break

                    if is_owner:
                        continue  # Skip owners from auction list

                    # Generate photo filename from player name
                    photo_filename = self._generate_photo_filename(full_name)

                    player = Player(
                        full_name=full_name,
                        contact_number=str(
                            row[CSV_COLUMNS["contact_number"]]
                        ).strip(),
                        batting_hand=str(row[CSV_COLUMNS["batting_hand"]]).strip(),
                        bowling_hand=str(row[CSV_COLUMNS["bowling_hand"]]).strip(),
                        primary_role=str(row[CSV_COLUMNS["primary_role"]]).strip(),
                        connection=str(row[CSV_COLUMNS["connection"]]).strip(),
                        photo_filename=photo_filename,
                        timestamp=str(row[CSV_COLUMNS["timestamp"]]),
                    )
                    players.append(player)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping invalid player row: {e}")
                    continue

            self.players = players
            logger.info(f"Successfully loaded {len(players)} players")
            return players

        except pd.errors.EmptyDataError:
            raise ValueError("CSV file is empty")
        except Exception as e:
            logger.error(f"Error loading players from CSV: {e}")
            raise

    def _generate_photo_filename(self, full_name: str) -> str:
        """
        Generate a photo filename from player's full name.

        Args:
            full_name: Player's full name

        Returns:
            Generated filename (e.g., "vaibhav_ahir.jpg")
        """
        # Convert to lowercase and replace spaces with underscores
        filename = full_name.lower().replace(" ", "_")
        # Remove special characters
        filename = "".join(c for c in filename if c.isalnum() or c == "_")
        return f"{filename}.jpg"

    def load_teams_from_config(
        self, config_path: Optional[Path] = None
    ) -> list[Team]:
        """
        Load teams from configuration file.

        Args:
            config_path: Path to the config JSON file. Uses default if not provided.

        Returns:
            List of Team objects
        """
        if config_path is None:
            config_path = TEAMS_CONFIG_PATH

        # If config file doesn't exist, create it with default teams
        if not config_path.exists():
            logger.info("Teams config not found, creating with defaults")
            self._create_default_teams_config(config_path)

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                teams_data = json.load(f)

            teams = []
            for team_data in teams_data:
                team = Team(
                    name=team_data["name"],
                    owner=team_data["owner"],
                    initial_budget=team_data["budget"],
                    remaining_budget=team_data["budget"],
                    logo_filename=team_data.get("logo", None),
                )
                teams.append(team)

            self.teams = teams
            logger.info(f"Successfully loaded {len(teams)} teams")
            return teams

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in teams config: {e}")
            raise ValueError(f"Invalid teams configuration file: {e}")
        except KeyError as e:
            logger.error(f"Missing required field in teams config: {e}")
            raise ValueError(f"Missing required field in teams config: {e}")

    def _create_default_teams_config(self, config_path: Path) -> None:
        """
        Create a default teams configuration file.

        Args:
            config_path: Path where the config file should be created
        """
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_TEAMS, f, indent=2)

        logger.info(f"Created default teams config at {config_path}")

    def save_teams_config(
        self, teams: list[Team], config_path: Optional[Path] = None
    ) -> None:
        """
        Save current teams configuration to file.

        Args:
            teams: List of Team objects to save
            config_path: Path to save the config file. Uses default if not provided.
        """
        if config_path is None:
            config_path = TEAMS_CONFIG_PATH

        teams_data = [
            {
                "name": team.name,
                "owner": team.owner,
                "budget": team.initial_budget,
            }
            for team in teams
        ]

        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(teams_data, f, indent=2)

        logger.info(f"Saved teams config to {config_path}")

    def export_auction_results(
        self, teams: list[Team], output_path: Optional[Path] = None
    ) -> None:
        """
        Export auction results to a CSV file.

        Args:
            teams: List of Team objects with auction results
            output_path: Path to save the results. Uses default if not provided.
        """
        if output_path is None:
            output_path = DATA_DIR / "auction_results.csv"

        results = []
        for team in teams:
            for player in team.players:
                results.append(
                    {
                        "Team": team.name,
                        "Owner": team.owner,
                        "Player Name": player.full_name,
                        "Price": player.sold_price,
                        "Role": player.primary_role,
                        "Batting Hand": player.batting_hand,
                        "Bowling Hand": player.bowling_hand,
                        "Contact": player.contact_number,
                    }
                )

        df = pd.DataFrame(results)
        df.to_csv(output_path, index=False)
        logger.info(f"Exported auction results to {output_path}")

    def export_team_wise(self, teams: list[Team]) -> None:
        """
        Export auction results as separate CSV files for each team.

        Args:
            teams: List of Team objects with auction results
        """
        for team in teams:
            output_path = DATA_DIR / f"{team.name.replace(' ', '_')}_roster.csv"

            players_data = []
            for player in team.players:
                players_data.append(
                    {
                        "Player Name": player.full_name,
                        "Price": player.sold_price,
                        "Role": player.primary_role,
                        "Batting Hand": player.batting_hand,
                        "Bowling Hand": player.bowling_hand,
                        "Connection": player.connection,
                        "Contact": player.contact_number,
                    }
                )

            if players_data:
                df = pd.DataFrame(players_data)
                df.to_csv(output_path, index=False)
                logger.info(f"Exported {team.name} roster to {output_path}")

    def export_all_players(self, teams: list[Team], unsold_players: list[Player]) -> None:
        """
        Export complete player list with sold/unsold status.

        Args:
            teams: List of Team objects
            unsold_players: List of unsold players
        """
        output_path = DATA_DIR / "all_players_status.csv"

        all_players_data = []

        # Add all players from teams (includes owners and auctioned players)
        for team in teams:
            for player in team.players:
                # Determine status
                if player.primary_role == "Team Owner":
                    status = "OWNER"
                    price = 0
                else:
                    status = "SOLD"
                    price = player.sold_price

                all_players_data.append(
                    {
                        "Player Name": player.full_name,
                        "Status": status,
                        "Team": team.name,
                        "Price": price,
                        "Role": player.primary_role,
                        "Batting Hand": player.batting_hand,
                        "Bowling Hand": player.bowling_hand,
                        "Connection": player.connection,
                        "Contact": player.contact_number,
                    }
                )

        # Add unsold players
        for player in unsold_players:
            all_players_data.append(
                {
                    "Player Name": player.full_name,
                    "Status": "UNSOLD",
                    "Team": "-",
                    "Price": 0,
                    "Role": player.primary_role,
                    "Batting Hand": player.batting_hand,
                    "Bowling Hand": player.bowling_hand,
                    "Connection": player.connection,
                    "Contact": player.contact_number,
                }
            )

        df = pd.DataFrame(all_players_data)
        df.to_csv(output_path, index=False)
        logger.info(f"Exported all players status to {output_path}")

    def get_team_by_name(self, team_name: str) -> Optional[Team]:
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

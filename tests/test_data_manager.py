"""Tests for the DataManager class."""

import csv
import json
import tempfile
from pathlib import Path

import pytest

from data_manager import DataManager
from models import Player, Team


def write_csv(path: Path, rows: list[dict]):
    """Helper to write a minimal player CSV file."""
    headers = [
        "Timestamp",
        "Full Name",
        "Contact Number (WhatsApp preferred)",
        "Select your batting hand and bowling arm [Batting Hand]",
        "Select your batting hand and bowling arm [Bowling Hand]",
        "What is your primary role on the pitch?",
        "What is your connection to the league?",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def sample_row(name="Alice", contact="9000000001"):
    return {
        "Timestamp": "1/1/2026 10:00:00",
        "Full Name": name,
        "Contact Number (WhatsApp preferred)": contact,
        "Select your batting hand and bowling arm [Batting Hand]": "Right",
        "Select your batting hand and bowling arm [Bowling Hand]": "Right",
        "What is your primary role on the pitch?": "Batsman",
        "What is your connection to the league?": "Local",
    }


class TestLoadPlayersFromCsv:
    def test_loads_players(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "players.csv"
            write_csv(csv_path, [sample_row("Alice"), sample_row("Bob", "9000000002")])

            manager = DataManager()
            players = manager.load_players_from_csv(csv_path=csv_path)

            assert len(players) == 2
            assert players[0].full_name == "Alice"

    def test_excludes_owners(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "players.csv"
            write_csv(
                csv_path,
                [
                    sample_row("Alice Owner"),
                    sample_row("Bob", "9000000002"),
                ],
            )

            manager = DataManager()
            players = manager.load_players_from_csv(
                csv_path=csv_path, exclude_owners=["Alice Owner"]
            )

            assert len(players) == 1
            assert players[0].full_name == "Bob"

    def test_missing_file_raises(self):
        manager = DataManager()
        with pytest.raises(FileNotFoundError):
            manager.load_players_from_csv(csv_path=Path("/nonexistent/path.csv"))

    def test_generates_photo_filename(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "players.csv"
            write_csv(csv_path, [sample_row("John Smith")])

            manager = DataManager()
            players = manager.load_players_from_csv(csv_path=csv_path)

            assert players[0].photo_filename == "john_smith.jpg"


class TestLoadTeamsFromConfig:
    def test_loads_teams(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config = [
                {"name": "Team A", "owner": "Owner A", "budget": 50000},
                {"name": "Team B", "owner": "Owner B", "budget": 30000},
            ]
            config_path.write_text(json.dumps(config))

            manager = DataManager()
            teams = manager.load_teams_from_config(config_path=config_path)

            assert len(teams) == 2
            assert teams[0].name == "Team A"
            assert teams[1].remaining_budget == 30000

    def test_loads_logo_filename(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config = [
                {
                    "name": "Team A",
                    "owner": "Owner A",
                    "budget": 50000,
                    "logo": "team_a.png",
                }
            ]
            config_path.write_text(json.dumps(config))

            manager = DataManager()
            teams = manager.load_teams_from_config(config_path=config_path)

            assert teams[0].logo_filename == "team_a.png"

    def test_invalid_json_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text("not valid json")

            manager = DataManager()
            with pytest.raises(ValueError):
                manager.load_teams_from_config(config_path=config_path)


class TestGeneratePhotoFilename:
    def test_basic(self):
        manager = DataManager()
        assert manager._generate_photo_filename("Vaibhav Ahir") == "vaibhav_ahir.jpg"

    def test_multiple_words(self):
        manager = DataManager()
        assert manager._generate_photo_filename("John Michael Smith") == "john_michael_smith.jpg"

    def test_special_characters_stripped(self):
        manager = DataManager()
        result = manager._generate_photo_filename("O'Brien")
        assert "'" not in result

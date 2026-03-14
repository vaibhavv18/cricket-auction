"""Tests for the AuctionManager class."""

import pytest

from auction_logic import AuctionManager
from models import Player, Team


def make_player(name, contact="9000000001"):
    return Player(
        full_name=name,
        contact_number=contact,
        batting_hand="Right",
        bowling_hand="Right",
        primary_role="Batsman",
        connection="Local",
    )


def make_team(name="Team A", owner="Owner A", budget=50000):
    return Team(
        name=name,
        owner=owner,
        initial_budget=budget,
        remaining_budget=budget,
    )


def make_auction(num_players=5, num_teams=2):
    players = [make_player(f"Player {i}", f"900000000{i}") for i in range(num_players)]
    teams = [make_team(f"Team {chr(65 + i)}", f"Owner {i}") for i in range(num_teams)]
    return AuctionManager(players, teams), players, teams


class TestAuctionManagerInit:
    def test_player_count(self):
        manager, players, _ = make_auction(num_players=5)
        assert len(manager.all_players) == 5

    def test_team_count(self):
        manager, _, teams = make_auction(num_teams=3)
        assert len(manager.teams) == 3

    def test_initial_round(self):
        manager, _, _ = make_auction()
        assert manager.state.current_round == 1

    def test_not_complete_at_start(self):
        manager, _, _ = make_auction()
        assert not manager.state.is_auction_complete


class TestGetNextPlayer:
    def test_returns_player(self):
        manager, _, _ = make_auction(num_players=3)
        player = manager.get_next_player()
        assert player is not None
        assert isinstance(player, Player)

    def test_decrements_remaining(self):
        manager, _, _ = make_auction(num_players=3)
        initial_count = len(manager.state.remaining_players)
        manager.get_next_player()
        assert len(manager.state.remaining_players) == initial_count - 1

    def test_sets_current_player(self):
        manager, _, _ = make_auction(num_players=3)
        player = manager.get_next_player()
        assert manager.state.current_player == player

    def test_returns_none_when_exhausted(self):
        # Auction ends only when all players are sold (no unsold queue remaining).
        manager, _, teams = make_auction(num_players=1)
        manager.get_next_player()
        manager.sell_player(teams[0].name, 500)
        result = manager.get_next_player()
        assert result is None
        assert manager.state.is_auction_complete


class TestSellPlayer:
    def test_sell_success(self):
        manager, _, teams = make_auction()
        manager.get_next_player()
        success, msg = manager.sell_player(teams[0].name, 1000)
        assert success
        assert teams[0].get_player_count() == 1

    def test_sell_reduces_budget(self):
        manager, _, teams = make_auction()
        initial_budget = teams[0].remaining_budget
        manager.get_next_player()
        manager.sell_player(teams[0].name, 2000)
        assert teams[0].remaining_budget == initial_budget - 2000

    def test_sell_no_current_player(self):
        manager, _, teams = make_auction()
        success, msg = manager.sell_player(teams[0].name, 1000)
        assert not success

    def test_sell_invalid_team(self):
        manager, _, _ = make_auction()
        manager.get_next_player()
        success, msg = manager.sell_player("Nonexistent Team", 1000)
        assert not success

    def test_sell_exceeds_budget(self):
        manager, _, teams = make_auction()
        manager.get_next_player()
        success, msg = manager.sell_player(teams[0].name, 999999)
        assert not success


class TestMarkUnsold:
    def test_unsold_adds_to_list(self):
        manager, _, _ = make_auction(num_players=3)
        manager.get_next_player()
        manager.mark_unsold()
        assert len(manager.state.unsold_players) == 1

    def test_unsold_no_player(self):
        manager, _, _ = make_auction()
        success, _ = manager.mark_unsold()
        assert not success


class TestSellbackHighestPlayer:
    def test_sellback_refunds_50_percent(self):
        manager, _, teams = make_auction()
        manager.get_next_player()
        manager.sell_player(teams[0].name, 10000)
        budget_before = teams[0].remaining_budget

        success, msg, player = manager.sellback_highest_player(teams[0])

        assert success
        assert teams[0].remaining_budget == budget_before + 5000

    def test_sellback_puts_player_back_in_pool(self):
        manager, _, teams = make_auction()
        manager.get_next_player()
        manager.sell_player(teams[0].name, 10000)
        remaining_before = len(manager.state.remaining_players)

        manager.sellback_highest_player(teams[0])

        assert len(manager.state.remaining_players) == remaining_before + 1

    def test_sellback_empty_team(self):
        manager, _, teams = make_auction()
        success, msg, player = manager.sellback_highest_player(teams[0])
        assert not success
        assert player is None


class TestResetAuction:
    def test_reset_restores_budget(self):
        manager, _, teams = make_auction()
        initial_budget = teams[0].remaining_budget
        manager.get_next_player()
        manager.sell_player(teams[0].name, 5000)
        manager.reset_auction()
        assert teams[0].remaining_budget == initial_budget

    def test_reset_clears_squad(self):
        manager, _, teams = make_auction()
        manager.get_next_player()
        manager.sell_player(teams[0].name, 5000)
        manager.reset_auction()
        assert teams[0].get_player_count() == 0

    def test_reset_resets_round(self):
        manager, _, _ = make_auction()
        manager.state.current_round = 3
        manager.reset_auction()
        assert manager.state.current_round == 1


class TestGetAuctionStatistics:
    def test_initial_statistics(self):
        manager, players, _ = make_auction(num_players=5)
        stats = manager.get_auction_statistics()
        assert stats["total_players"] == 5
        assert stats["sold_players"] == 0
        assert stats["current_round"] == 1

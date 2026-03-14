"""Tests for Player, Team, and AuctionState data models."""

import pytest

from models import AuctionState, Player, Team


def make_player(name="John Doe", contact="9000000001"):
    return Player(
        full_name=name,
        contact_number=contact,
        batting_hand="Right",
        bowling_hand="Right",
        primary_role="Batsman",
        connection="Local",
    )


def make_team(name="Team A", owner="Owner A", budget=10000):
    return Team(
        name=name,
        owner=owner,
        initial_budget=budget,
        remaining_budget=budget,
    )


class TestPlayer:
    def test_creation(self):
        player = make_player()
        assert player.full_name == "John Doe"
        assert not player.is_sold

    def test_empty_name_raises(self):
        with pytest.raises(ValueError):
            Player(
                full_name="",
                contact_number="9000000001",
                batting_hand="Right",
                bowling_hand="Right",
                primary_role="Batsman",
                connection="Local",
            )

    def test_empty_contact_raises(self):
        with pytest.raises(ValueError):
            Player(
                full_name="John Doe",
                contact_number="",
                batting_hand="Right",
                bowling_hand="Right",
                primary_role="Batsman",
                connection="Local",
            )

    def test_mark_sold(self):
        player = make_player()
        player.mark_sold("Team A", 5000)
        assert player.is_sold
        assert player.sold_to == "Team A"
        assert player.sold_price == 5000

    def test_mark_unsold(self):
        player = make_player()
        player.mark_sold("Team A", 5000)
        player.mark_unsold()
        assert not player.is_sold
        assert player.sold_to is None
        assert player.sold_price == 0


class TestTeam:
    def test_creation(self):
        team = make_team()
        assert team.name == "Team A"
        assert team.remaining_budget == 10000
        assert team.get_player_count() == 0

    def test_empty_name_raises(self):
        with pytest.raises(ValueError):
            Team(name="", owner="Owner", initial_budget=1000, remaining_budget=1000)

    def test_zero_budget_raises(self):
        with pytest.raises(ValueError):
            Team(name="Team A", owner="Owner", initial_budget=0, remaining_budget=0)

    def test_add_player_success(self):
        team = make_team(budget=10000)
        player = make_player()
        result = team.add_player(player, 3000)
        assert result is True
        assert team.remaining_budget == 7000
        assert team.get_player_count() == 1
        assert player.is_sold

    def test_add_player_insufficient_budget(self):
        team = make_team(budget=1000)
        player = make_player()
        result = team.add_player(player, 5000)
        assert result is False
        assert team.get_player_count() == 0

    def test_get_total_spent(self):
        team = make_team(budget=10000)
        player = make_player()
        team.add_player(player, 4000)
        assert team.get_total_spent() == 4000

    def test_remove_player(self):
        team = make_team(budget=10000)
        player = make_player()
        team.add_player(player, 3000)
        result = team.remove_player(player)
        assert result is True
        assert team.get_player_count() == 0

    def test_remove_player_not_in_team(self):
        team = make_team()
        player = make_player()
        result = team.remove_player(player)
        assert result is False

    def test_get_highest_bid_player(self):
        team = make_team(budget=20000)
        p1 = make_player("Alice", "9000000001")
        p2 = make_player("Bob", "9000000002")
        team.add_player(p1, 3000)
        team.add_player(p2, 7000)
        highest = team.get_highest_bid_player()
        assert highest.full_name == "Bob"

    def test_get_highest_bid_player_empty_team(self):
        team = make_team()
        assert team.get_highest_bid_player() is None


class TestAuctionState:
    def test_default_state(self):
        state = AuctionState()
        assert state.current_round == 1
        assert state.current_player is None
        assert not state.is_auction_complete

    def test_has_players_remaining_with_players(self):
        p = make_player()
        state = AuctionState(remaining_players=[p])
        assert state.has_players_remaining()

    def test_has_players_remaining_empty(self):
        state = AuctionState()
        assert not state.has_players_remaining()

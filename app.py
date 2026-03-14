"""
Streamlit application for the Cricket Auction Management System.

Run with: streamlit run app.py
"""

import logging
import random
import time
from pathlib import Path
from typing import Optional

import streamlit as st
from PIL import Image

from auction_logic import AuctionManager
from config import (
    ANIMATION_DURATION,
    ANIMATION_PLAYER_COUNT,
    DEFAULT_PLAYER_IMAGE,
    IMAGES_DIR,
    IMAGE_WIDTH,
    LEAGUE_NAME,
    LEAGUE_SEASON,
    MIN_BID_AMOUNT,
    REQUIRED_PLAYERS_PER_TEAM,
    TEAM_COLORS,
)
from data_manager import DataManager
from models import Player

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title=f"{LEAGUE_NAME} Auction",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)


def initialize_session_state():
    """Initialize Streamlit session state on first load."""
    if "initialized" in st.session_state:
        return

    try:
        data_manager = DataManager()
        teams = data_manager.load_teams_from_config()
        owner_names = [team.owner for team in teams]

        all_players = data_manager.load_players_from_csv(exclude_owners=[])

        owner_lookup = {}
        for player in all_players:
            for team in teams:
                if team.owner.lower() in player.full_name.lower():
                    owner_lookup[team.owner] = player
                    break

        auction_players = [
            p for p in all_players
            if not any(owner.lower() in p.full_name.lower() for owner in owner_names)
        ]

        auction_manager = AuctionManager(auction_players, teams)

        for team in auction_manager.teams:
            if team.owner in owner_lookup:
                owner_player = owner_lookup[team.owner]
                owner_player.primary_role = "Team Owner"
                owner_player.mark_sold(team.name, 0)
                team.players.insert(0, owner_player)
            else:
                logger.warning("Owner %s not found in player.csv", team.owner)

        logger.info(
            "Initialized with %d auction players across %d teams",
            len(auction_players),
            len(teams),
        )

        st.session_state.data_manager = data_manager
        st.session_state.auction_manager = auction_manager
        st.session_state.initialized = True
        st.session_state.current_view = "auction"
        st.session_state.selected_team_for_detail = None

    except Exception as exc:
        st.error(f"Failed to initialize application: {exc}")
        logger.error("Initialization error: %s", exc)
        st.stop()


def load_team_logo(logo_filename: Optional[str]) -> Optional[Image.Image]:
    """Load a team logo from the images directory."""
    if not logo_filename:
        return None

    logo_path = IMAGES_DIR / logo_filename
    try:
        if logo_path.exists():
            return Image.open(logo_path)

        base = logo_filename.rsplit(".", 1)[0]
        for ext in (".png", ".jpg", ".jpeg"):
            alt = IMAGES_DIR / f"{base}{ext}"
            if alt.exists():
                return Image.open(alt)

        return None
    except Exception as exc:
        logger.warning("Could not load logo %s: %s", logo_filename, exc)
        return None


def load_player_image(photo_filename: str) -> Image.Image:
    """Load a player photo, falling back to a placeholder if not found."""
    image_path = IMAGES_DIR / photo_filename
    default_path = IMAGES_DIR / DEFAULT_PLAYER_IMAGE

    try:
        if image_path.exists():
            return Image.open(image_path)

        alt_filename = None
        if photo_filename.lower().endswith(".jpg"):
            alt_filename = photo_filename[:-4] + ".jpeg"
        elif photo_filename.lower().endswith(".jpeg"):
            alt_filename = photo_filename[:-5] + ".jpg"

        if alt_filename:
            alt_path = IMAGES_DIR / alt_filename
            if alt_path.exists():
                return Image.open(alt_path)

        if default_path.exists():
            return Image.open(default_path)

        return Image.new("RGB", (400, 400), color=(200, 200, 200))

    except Exception as exc:
        logger.warning("Could not load image %s: %s", photo_filename, exc)
        return Image.new("RGB", (400, 400), color=(200, 200, 200))


def show_random_player_animation():
    """Show a brief animation before revealing the next player."""
    auction_manager = st.session_state.auction_manager

    if auction_manager.state.current_player is not None:
        current = auction_manager.state.current_player
        if current not in auction_manager.state.auctioned_in_current_round:
            logger.info("Auto-marking %s as unsold (skipped)", current.full_name)
            auction_manager.mark_unsold(current)

    animation_pool = auction_manager.get_random_animation_pool()

    if not animation_pool:
        st.warning("No players available.")
        return

    placeholder = st.empty()

    for _ in range(12):
        player = random.choice(animation_pool)
        with placeholder.container():
            st.markdown(
                f"""
                <div style="
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100px;
                    margin: 10px 0;
                ">
                    <div style="
                        background: linear-gradient(90deg, #667eea88 0%, #764ba288 100%);
                        padding: 15px 40px;
                        border-radius: 30px;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                        display: inline-block;
                    ">
                        <span style="
                            color: white;
                            font-size: 20px;
                            font-weight: bold;
                            white-space: nowrap;
                        ">{player.full_name}</span>
                        <span style="
                            color: #f0f0f0;
                            font-size: 14px;
                            margin-left: 15px;
                            white-space: nowrap;
                        ">{player.primary_role}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        time.sleep(0.12)

    auction_manager.get_next_player()
    placeholder.empty()


def render_sidebar():
    """Render the sidebar with team summaries and budget information."""
    st.sidebar.title("Teams and Budgets")

    auction_manager = st.session_state.auction_manager
    teams_summary = auction_manager.get_teams_summary()
    budget_issues = auction_manager.check_team_budget_issues()

    for idx, team_summary in enumerate(teams_summary):
        color = TEAM_COLORS[idx % len(TEAM_COLORS)]
        team = auction_manager.teams[idx]

        is_complete, _ = auction_manager.validate_team_completion(team)
        has_budget_issue = any(
            issue["team"].name == team_summary["name"] for issue in budget_issues
        )

        with st.sidebar.container():
            logo_img = load_team_logo(team.logo_filename)

            col_logo, col_info = st.sidebar.columns([1, 4])
            with col_logo:
                if logo_img:
                    st.image(logo_img, width=50)
                else:
                    status = "OK" if is_complete else ("!" if has_budget_issue else "-")
                    st.markdown(
                        f"<div style='font-weight:bold; color:{color};'>{status}</div>",
                        unsafe_allow_html=True,
                    )

            with col_info:
                st.markdown(
                    f"""
                    <div style="
                        background-color: {color}20;
                        border-left: 4px solid {color};
                        padding: 10px;
                        border-radius: 5px;
                    ">
                        <h3 style="margin: 0; color: {color};">{team_summary['name']}</h3>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            if st.sidebar.button(
                team_summary["owner"],
                key=f"owner_{idx}",
                use_container_width=True,
            ):
                st.session_state.current_view = "owner_detail"
                st.session_state.selected_team_for_detail = team
                st.rerun()

            st.sidebar.markdown(
                f"""
                <div style="padding: 5px 10px; font-size: 14px;">
                    <p style="margin: 5px 0;"><b>Budget left:</b> Rs.{team_summary['remaining_budget']:,}</p>
                    <p style="margin: 5px 0;"><b>Spent:</b> Rs.{team_summary['total_spent']:,}</p>
                    <p style="margin: 5px 0; {'color: green;' if is_complete else 'color: orange;'}">
                        <b>Players:</b> {team_summary['player_count']}/{REQUIRED_PLAYERS_PER_TEAM}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.sidebar.expander(f"View {team_summary['name']} Roster"):
                players = team_summary["players"]
                if not players:
                    st.info("No players yet.")
                    continue

                owner = next(
                    (p for p in players if p.primary_role == "Team Owner"), None
                )
                regular = [p for p in players if p.primary_role != "Team Owner"]

                if owner:
                    st.markdown(
                        f"**Team Owner**\n\n"
                        f"**Name:** {owner.full_name}\n\n"
                        f"**Batting:** {owner.batting_hand} | **Bowling:** {owner.bowling_hand}"
                    )
                    st.divider()

                if regular:
                    st.markdown("**Squad**")
                    for i, player in enumerate(regular, 1):
                        st.markdown(
                            f"{i}. **{player.full_name}** "
                            f"({player.primary_role}) — "
                            f"Rs.{player.sold_price:,}"
                        )
                else:
                    st.info("No players purchased yet.")

    if budget_issues:
        st.sidebar.divider()
        st.sidebar.warning("Budget issues detected")
        for issue in budget_issues:
            with st.sidebar.expander(f"{issue['team'].name} — Action Required"):
                st.markdown(
                    f"**Problem:** Not enough budget to complete the squad.\n\n"
                    f"- Players still needed: {issue['players_needed']}\n"
                    f"- Current budget: Rs.{issue['budget']:,}\n"
                    f"- Minimum bid: Rs.{MIN_BID_AMOUNT:,}\n\n"
                    f"**Fix:** Sell back the highest player.\n\n"
                    f"- Player: {issue['highest_player']}\n"
                    f"- Original price: Rs.{issue['highest_bid']:,}\n"
                    f"- Refund (50%): Rs.{issue['refund_if_sold']:,}"
                )

                if st.button(
                    f"Sell back {issue['highest_player']}",
                    key=f"sellback_{issue['team'].name}",
                ):
                    success, msg, _ = auction_manager.sellback_highest_player(
                        issue["team"]
                    )
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)


def render_auction_stats():
    """Render the top-level auction statistics bar."""
    auction_manager = st.session_state.auction_manager
    stats = auction_manager.get_auction_statistics()

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Round", stats["current_round"])
    with col2:
        st.metric("Total Players", stats["total_players"])
    with col3:
        st.metric("Sold", stats["sold_players"])
    with col4:
        st.metric("Remaining", stats["remaining_players"])
    with col5:
        st.metric("Unsold (Next Round)", stats["unsold_players"])


def render_current_player():
    """Render the player currently up for auction."""
    auction_manager = st.session_state.auction_manager
    current_player = auction_manager.state.current_player

    if current_player is None:
        st.info("Click 'Next Player' to start the auction.")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Player Photo")
        if current_player.photo_filename:
            image = load_player_image(current_player.photo_filename)
            st.image(image, width=IMAGE_WIDTH, use_container_width=False)
        else:
            st.info("No photo available.")

    with col2:
        st.subheader("Player Details")
        st.markdown(
            f"### {current_player.full_name}\n\n"
            f"**Contact:** {current_player.contact_number}\n\n"
            f"**Role:** {current_player.primary_role}\n\n"
            f"**Batting Hand:** {current_player.batting_hand}\n\n"
            f"**Bowling Hand:** {current_player.bowling_hand}\n\n"
            f"**Connection:** {current_player.connection}"
        )


def render_bidding_controls():
    """Render the team selector, bid input, and SOLD/UNSOLD buttons."""
    auction_manager = st.session_state.auction_manager
    current_player = auction_manager.state.current_player

    if current_player is None:
        return

    st.subheader("Auction Controls")

    col1, col2 = st.columns(2)

    with col1:
        team_names = [team.name for team in auction_manager.teams]
        selected_team = st.selectbox("Select Team", team_names, key="team_selector")

    with col2:
        bid_amount = st.number_input(
            f"Bid Amount (Rs.) — Minimum Rs.{MIN_BID_AMOUNT:,}",
            min_value=MIN_BID_AMOUNT,
            value=MIN_BID_AMOUNT,
            step=500,
            key="bid_amount",
        )

    col_sold, col_unsold, _ = st.columns([1, 1, 2])

    with col_sold:
        if st.button("SOLD", type="primary", use_container_width=True):
            if bid_amount < MIN_BID_AMOUNT:
                st.error(f"Bid must be at least Rs.{MIN_BID_AMOUNT:,}.")
            else:
                success, message = auction_manager.sell_player(selected_team, bid_amount)
                if success:
                    st.success(message)
                    st.balloons()
                else:
                    st.error(message)

    with col_unsold:
        if st.button("UNSOLD", type="secondary", use_container_width=True):
            success, message = auction_manager.mark_unsold()
            if success:
                st.warning(message)
            else:
                st.error(message)


def render_navigation():
    """Render the navigation and export controls at the bottom of the page."""
    st.divider()

    _, col_next, col_reset, col_export_type, col_export_btn = st.columns(
        [2, 1, 1, 1, 1]
    )

    with col_next:
        if st.button("Next Player", use_container_width=True):
            show_random_player_animation()
            st.rerun()

    with col_reset:
        if st.button("Reset Auction", use_container_width=True):
            st.session_state.auction_manager.reset_auction()
            st.rerun()

    with col_export_type:
        export_option = st.selectbox(
            "Export",
            ["Overall Results", "Team-wise", "All Players Status"],
            key="export_option",
            label_visibility="collapsed",
        )

    with col_export_btn:
        if st.button("Export", use_container_width=True):
            data_manager = st.session_state.data_manager
            auction_manager = st.session_state.auction_manager

            try:
                if export_option == "Overall Results":
                    data_manager.export_auction_results(auction_manager.teams)
                    st.success("Exported to data/auction_results.csv")
                elif export_option == "Team-wise":
                    data_manager.export_team_wise(auction_manager.teams)
                    st.success("Exported team rosters to data/")
                elif export_option == "All Players Status":
                    data_manager.export_all_players(
                        auction_manager.teams,
                        auction_manager.state.unsold_players,
                    )
                    st.success("Exported to data/all_players_status.csv")
            except Exception as exc:
                st.error(f"Export failed: {exc}")


def render_owner_detail_page():
    """Render the owner detail page showing team roster with photos."""
    team = st.session_state.selected_team_for_detail

    if team is None:
        st.error("No team selected.")
        if st.button("Back to Auction"):
            st.session_state.current_view = "auction"
            st.rerun()
        return

    if st.button("Back to Auction", key="back_top"):
        st.session_state.current_view = "auction"
        st.rerun()

    st.title(team.name)

    logo_img = load_team_logo(team.logo_filename)
    if logo_img:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(logo_img, width=200)

    st.divider()

    owner = next((p for p in team.players if p.primary_role == "Team Owner"), None)
    regular_players = [p for p in team.players if p.primary_role != "Team Owner"]

    if owner:
        st.header("Team Owner")

        col1, col2 = st.columns([1, 2])

        with col1:
            owner_img = load_player_image(owner.photo_filename)
            st.image(owner_img, width=250)

        with col2:
            st.markdown(
                f"### {owner.full_name}\n\n"
                f"**Contact:** {owner.contact_number}\n\n"
                f"**Batting Hand:** {owner.batting_hand}\n\n"
                f"**Bowling Hand:** {owner.bowling_hand}\n\n"
                f"**Connection:** {owner.connection}"
            )

    st.divider()
    st.header("Team Stats")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Players", len(team.players))
    with col2:
        st.metric("Budget Remaining", f"Rs.{team.remaining_budget:,}")
    with col3:
        st.metric("Total Spent", f"Rs.{team.get_total_spent():,}")

    st.divider()

    if regular_players:
        st.subheader(f"Squad ({len(regular_players)} players)")

        for i in range(0, len(regular_players), 3):
            cols = st.columns(3)
            for j, col in enumerate(cols):
                if i + j >= len(regular_players):
                    break
                player = regular_players[i + j]
                with col:
                    player_img = load_player_image(player.photo_filename)
                    st.image(player_img, use_container_width=True)

                    st.markdown(
                        f"""
                        <div style="
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            padding: 10px;
                            border-radius: 10px;
                            text-align: center;
                            color: white;
                            margin-bottom: 20px;
                        ">
                            <h4 style="margin: 5px 0; font-size: 16px;">{player.full_name}</h4>
                            <p style="margin: 3px 0; font-size: 12px;">{player.primary_role}</p>
                            <p style="margin: 3px 0; font-size: 12px;">
                                {player.batting_hand} bat | {player.bowling_hand} bowl
                            </p>
                            <p style="margin: 3px 0; font-size: 14px; font-weight: bold;">
                                Rs.{player.sold_price:,}
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
    else:
        st.info("No players in the squad yet.")

    st.divider()

    if st.button("Back to Auction", key="back_bottom"):
        st.session_state.current_view = "auction"
        st.rerun()


def main():
    """Entry point for the Streamlit application."""
    initialize_session_state()

    if st.session_state.current_view == "owner_detail":
        render_owner_detail_page()
        return

    st.title(f"{LEAGUE_NAME} — Auction")
    if LEAGUE_SEASON:
        st.markdown(f"##### {LEAGUE_SEASON}")

    render_sidebar()
    render_auction_stats()
    st.divider()

    auction_manager = st.session_state.auction_manager

    if auction_manager.state.is_auction_complete:
        st.success("Auction complete. All players have been auctioned.")

        incomplete = []
        for team in auction_manager.teams:
            is_ok, msg = auction_manager.validate_team_completion(team)
            if not is_ok:
                incomplete.append((team, msg))

        if incomplete:
            st.warning("Some teams do not have the required number of players.")
            for _, msg in incomplete:
                st.error(msg)

        if st.button("Start New Auction"):
            auction_manager.reset_auction()
            st.rerun()

        st.subheader("Final Rosters")
        for team_summary in auction_manager.get_teams_summary():
            with st.expander(
                f"{team_summary['name']} — "
                f"{team_summary['player_count']}/{REQUIRED_PLAYERS_PER_TEAM} players"
            ):
                if team_summary["players"]:
                    for player in team_summary["players"]:
                        st.markdown(
                            f"- **{player.full_name}** "
                            f"({player.primary_role}) — "
                            f"Rs.{player.sold_price:,}"
                        )
                else:
                    st.info("No players in this team.")
        return

    render_current_player()
    st.divider()
    render_bidding_controls()
    render_navigation()


if __name__ == "__main__":
    main()

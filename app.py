"""
Enhanced Streamlit application for the Auction Management System.

New features:
- Random player animation
- Team validation (14 players required)
- Budget recovery mechanism
- Multiple export formats
- Session persistence
- Minimum bid: ₹500 for all players

Run with: streamlit run app.py
"""

import logging
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration - Set to wide mode with longer session timeout
st.set_page_config(
    page_title=f"{LEAGUE_NAME} Auction",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Increase session timeout (browser-based, stays active as long as browser is open)
# Streamlit sessions persist as long as the browser tab is open


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "initialized" not in st.session_state:
        try:
            # Load data
            data_manager = DataManager()
            teams = data_manager.load_teams_from_config()

            # Get list of owner names
            owner_names = [team.owner for team in teams]

            # Load ALL players from CSV first (including owners)
            all_players_data = data_manager.load_players_from_csv(exclude_owners=[])

            # Create owner lookup dictionary using fuzzy matching
            owner_lookup = {}
            for player in all_players_data:
                for team in teams:
                    # Case-insensitive partial match (same logic as data_manager)
                    if team.owner.lower() in player.full_name.lower():
                        owner_lookup[team.owner] = player
                        logger.info(f"Found owner in CSV: {player.full_name} for team {team.name}")
                        break

            # Filter out owners from auction pool
            players = [
                p for p in all_players_data
                if not any(owner.lower() in p.full_name.lower() for owner in owner_names)
            ]

            # Initialize auction manager
            auction_manager = AuctionManager(players, teams)

            # Add real owner Player objects to their respective teams
            for team in auction_manager.teams:
                if team.owner in owner_lookup:
                    # Use the actual owner data from CSV
                    owner_player = owner_lookup[team.owner]
                    owner_player.primary_role = "Team Owner"  # Override role to mark as owner
                    owner_player.mark_sold(team.name, 0)
                    team.players.insert(0, owner_player)  # Add owner at the beginning
                    logger.info(f"Added owner {owner_player.full_name} to {team.name} with real CSV data")
                else:
                    logger.warning(f"Owner {team.owner} not found in player.csv - team may be incomplete")

            logger.info(f"Application initialized successfully with {len(players)} auctionable players")
            logger.info(f"Added {len(owner_lookup)} team owners to their respective teams")

            # Store in session state
            st.session_state.data_manager = data_manager
            st.session_state.auction_manager = auction_manager
            st.session_state.initialized = True
            st.session_state.show_animation = False
            st.session_state.animation_players = []
            st.session_state.current_view = "auction"  # Can be "auction" or "owner_detail"
            st.session_state.selected_team_for_detail = None

            logger.info("Application initialized successfully")

        except Exception as e:
            st.error(f"Error initializing application: {e}")
            logger.error(f"Initialization error: {e}")
            st.stop()


def load_team_logo(logo_filename: Optional[str]) -> Optional[Image.Image]:
    """
    Load team logo from the images directory.

    Supports both .png and .jpg/.jpeg extensions.

    Args:
        logo_filename: Name of the logo file

    Returns:
        PIL Image object or None if not found
    """
    if not logo_filename:
        return None

    logo_path = IMAGES_DIR / logo_filename

    try:
        # Try original filename
        if logo_path.exists():
            return Image.open(logo_path)

        # Try alternate extensions
        base_name = logo_filename.rsplit('.', 1)[0]
        for ext in ['.png', '.jpg', '.jpeg']:
            alternate_path = IMAGES_DIR / f"{base_name}{ext}"
            if alternate_path.exists():
                return Image.open(alternate_path)

        return None
    except Exception as e:
        logger.warning(f"Error loading logo {logo_filename}: {e}")
        return None


def load_player_image(photo_filename: str) -> Image.Image:
    """
    Load player image from the images directory.

    Supports both .jpg and .jpeg extensions.

    Args:
        photo_filename: Name of the image file

    Returns:
        PIL Image object
    """
    image_path = IMAGES_DIR / photo_filename
    default_image_path = IMAGES_DIR / DEFAULT_PLAYER_IMAGE

    try:
        # Try original filename (e.g., vaibhav_ahir.jpg)
        if image_path.exists():
            return Image.open(image_path)

        # Try alternate extension (.jpeg if original was .jpg, or vice versa)
        if photo_filename.lower().endswith('.jpg'):
            alternate_filename = photo_filename[:-4] + '.jpeg'
        elif photo_filename.lower().endswith('.jpeg'):
            alternate_filename = photo_filename[:-5] + '.jpg'
        else:
            alternate_filename = None

        if alternate_filename:
            alternate_path = IMAGES_DIR / alternate_filename
            if alternate_path.exists():
                return Image.open(alternate_path)

        # Try default image
        if default_image_path.exists():
            return Image.open(default_image_path)
        else:
            # Create a placeholder image
            return Image.new("RGB", (400, 400), color=(200, 200, 200))
    except Exception as e:
        logger.warning(f"Error loading image {photo_filename}: {e}")
        return Image.new("RGB", (400, 400), color=(200, 200, 200))


def show_random_player_animation():
    """Display random player selection animation."""
    auction_manager = st.session_state.auction_manager

    # If there's a current player who hasn't been auctioned, mark them as unsold
    if auction_manager.state.current_player is not None:
        current = auction_manager.state.current_player
        # Check if player is already in auctioned list (sold or unsold)
        if current not in auction_manager.state.auctioned_in_current_round:
            logger.info(f"Auto-marking {current.full_name} as unsold (skipped)")
            auction_manager.mark_unsold(current)

    # Get animation pool (excludes already auctioned players in current round)
    animation_pool = auction_manager.get_random_animation_pool()

    if not animation_pool:
        st.warning("No players available for animation")
        return

    # Animation placeholder
    animation_placeholder = st.empty()

    # Show rapid player changes
    for _ in range(12):  # Show 12 quick flashes
        import random
        random_player = random.choice(animation_pool)

        with animation_placeholder.container():
            st.markdown(
                f"""
                <div style='
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100px;
                    margin: 10px 0;
                '>
                    <div style='
                        background: linear-gradient(90deg, #667eea88 0%, #764ba288 100%);
                        padding: 15px 40px;
                        border-radius: 30px;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                        display: inline-block;
                    '>
                        <span style='
                            color: white;
                            font-size: 20px;
                            font-weight: bold;
                            white-space: nowrap;
                        '>🎲 {random_player.full_name}</span>
                        <span style='
                            color: #f0f0f0;
                            font-size: 14px;
                            margin-left: 15px;
                            white-space: nowrap;
                        '>• {random_player.primary_role}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        time.sleep(0.12)  # Fast animation

    # Final selection - just set player without showing text
    auction_manager.get_next_player()
    animation_placeholder.empty()


def render_sidebar():
    """Render the sidebar with team information."""
    st.sidebar.title("🏏 Teams & Budgets")

    auction_manager = st.session_state.auction_manager
    teams_summary = auction_manager.get_teams_summary()

    # Check for budget issues
    budget_issues = auction_manager.check_team_budget_issues()

    for idx, team_summary in enumerate(teams_summary):
        color = TEAM_COLORS[idx % len(TEAM_COLORS)]

        # Check team completion status
        is_complete, status_msg = auction_manager.validate_team_completion(
            auction_manager.teams[idx]
        )

        # Check if this team has budget issues
        has_budget_issue = any(
            issue["team"].name == team_summary["name"] for issue in budget_issues
        )

        with st.sidebar.container():
            # Add warning icon if incomplete or budget issue
            team_icon = "✅" if is_complete else ("⚠️" if has_budget_issue else "🏏")

            # Load team logo
            team = auction_manager.teams[idx]
            logo_img = load_team_logo(team.logo_filename)

            # Display team logo and name
            col_logo, col_info = st.sidebar.columns([1, 4])
            with col_logo:
                if logo_img:
                    st.image(logo_img, width=50)
                else:
                    st.markdown(f"<h2 style='margin: 0;'>{team_icon}</h2>", unsafe_allow_html=True)

            with col_info:
                st.markdown(
                    f"""
                    <div style='
                        background-color: {color}20;
                        border-left: 4px solid {color};
                        padding: 10px;
                        border-radius: 5px;
                    '>
                        <h3 style='margin: 0; color: {color};'>{team_summary['name']}</h3>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Owner button and team info
            if st.sidebar.button(f"👨‍💼 {team_summary['owner']}", key=f"owner_{idx}", use_container_width=True):
                st.session_state.current_view = "owner_detail"
                st.session_state.selected_team_for_detail = team
                st.rerun()

            st.sidebar.markdown(
                f"""
                <div style='padding: 5px 10px; font-size: 14px;'>
                    <p style='margin: 5px 0;'><b>Budget Left:</b> ₹{team_summary['remaining_budget']:,}</p>
                    <p style='margin: 5px 0;'><b>Spent:</b> ₹{team_summary['total_spent']:,}</p>
                    <p style='margin: 5px 0; {"color: green;" if is_complete else "color: orange;"}'>
                        <b>Players:</b> {team_summary['player_count']}/{REQUIRED_PLAYERS_PER_TEAM}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Show players in this team
            with st.sidebar.expander(f"👥 View {team_summary['name']} Roster"):
                if team_summary["players"]:
                    # First, show owner details prominently
                    owner = None
                    regular_players = []

                    for player in team_summary["players"]:
                        if player.primary_role == "Team Owner":
                            owner = player
                        else:
                            regular_players.append(player)

                    # Display owner information
                    if owner:
                        st.markdown(f"""
                        **👨‍💼 TEAM OWNER**

                        **Name:** {owner.full_name}
                        **Contact:** {owner.contact_number}
                        **Batting:** {owner.batting_hand} | **Bowling:** {owner.bowling_hand}
                        """)
                        st.divider()

                    # Display team roster
                    if regular_players:
                        st.markdown("**TEAM PLAYERS**")
                        for idx, player in enumerate(regular_players, 1):
                            st.markdown(
                                f"{idx}. **{player.full_name}** ({player.primary_role}) - ₹{player.sold_price:,}"
                            )
                    else:
                        st.info("No players purchased yet")
                else:
                    st.info("Team roster empty")

    # Show budget warning if any
    if budget_issues:
        st.sidebar.divider()
        st.sidebar.warning("⚠️ Budget Issues Detected")
        for issue in budget_issues:
            with st.sidebar.expander(f"{issue['team'].name} - Action Required"):
                st.markdown(f"""
                **Problem:** Insufficient budget for remaining players
                - Players needed: {issue['players_needed']}
                - Current budget: ₹{issue['budget']:,}
                - Minimum bid: ₹{MIN_BID_AMOUNT:,}

                **Solution:** Sell back highest player
                - Player: {issue['highest_player']}
                - Original price: ₹{issue['highest_bid']:,}
                - Refund (50%): ₹{issue['refund_if_sold']:,}
                """)

                if st.button(
                    f"Sell Back {issue['highest_player']}",
                    key=f"sellback_{issue['team'].name}",
                ):
                    success, msg, player = auction_manager.sellback_highest_player(
                        issue['team']
                    )
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)


def render_auction_stats():
    """Render auction statistics."""
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
    """Render the current player being auctioned."""
    auction_manager = st.session_state.auction_manager
    current_player = auction_manager.state.current_player

    if current_player is None:
        st.info("Click 'Next Player' to start the auction!")
        return

    # Create two columns: one for image, one for details
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Player Photo")
        if current_player.photo_filename:
            image = load_player_image(current_player.photo_filename)
            st.image(image, width=IMAGE_WIDTH, use_container_width=False)
        else:
            st.info("No photo available")

    with col2:
        st.subheader("Player Details")

        st.markdown(
            f"""
            ### {current_player.full_name}

            **Contact:** {current_player.contact_number}

            **Role:** {current_player.primary_role}

            **Batting Hand:** {current_player.batting_hand}

            **Bowling Hand:** {current_player.bowling_hand}

            **Connection:** {current_player.connection}
            """
        )


def render_bidding_controls():
    """Render the bidding controls."""
    auction_manager = st.session_state.auction_manager
    current_player = auction_manager.state.current_player

    if current_player is None:
        return

    st.subheader("Auction Controls")

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        # Team selection
        team_names = [team.name for team in auction_manager.teams]
        selected_team = st.selectbox(
            "Select Team",
            team_names,
            key="team_selector",
        )

    with col2:
        # Bid amount - minimum 500
        bid_amount = st.number_input(
            f"Bid Amount (₹) - Min: ₹{MIN_BID_AMOUNT:,}",
            min_value=MIN_BID_AMOUNT,
            value=MIN_BID_AMOUNT,
            step=500,
            key="bid_amount",
        )

    with col3:
        st.write("")  # Spacer
        st.write("")  # Spacer

    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("✅ SOLD", type="primary", use_container_width=True):
            # Validate bid is at least minimum amount
            if bid_amount < MIN_BID_AMOUNT:
                st.error(
                    f"Bid must be at least ₹{MIN_BID_AMOUNT:,}"
                )
            else:
                success, message = auction_manager.sell_player(
                    selected_team, bid_amount
                )
                if success:
                    st.success(message)
                    st.balloons()
                else:
                    st.error(message)

    with col2:
        if st.button("❌ UNSOLD", type="secondary", use_container_width=True):
            success, message = auction_manager.mark_unsold()
            if success:
                st.warning(message)
            else:
                st.error(message)


def render_navigation():
    """Render navigation controls."""
    st.divider()

    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

    with col1:
        st.write("")  # Spacer

    with col2:
        if st.button("⏭️ Next Player", use_container_width=True):
            show_random_player_animation()
            st.rerun()

    with col3:
        if st.button("🔄 Reset Auction", use_container_width=True):
            st.session_state.auction_manager.reset_auction()
            st.rerun()

    with col4:
        # Export dropdown
        export_option = st.selectbox(
            "Export",
            ["Overall Results", "Team-wise", "All Players Status"],
            key="export_option",
            label_visibility="collapsed",
        )

    with col5:
        if st.button("💾 Export", use_container_width=True):
            try:
                data_manager = st.session_state.data_manager
                auction_manager = st.session_state.auction_manager

                if export_option == "Overall Results":
                    data_manager.export_auction_results(auction_manager.teams)
                    st.success("✅ Exported to data/auction_results.csv")

                elif export_option == "Team-wise":
                    data_manager.export_team_wise(auction_manager.teams)
                    st.success("✅ Exported team rosters to data/")

                elif export_option == "All Players Status":
                    data_manager.export_all_players(
                        auction_manager.teams, auction_manager.state.unsold_players
                    )
                    st.success("✅ Exported to data/all_players_status.csv")

            except Exception as e:
                st.error(f"Error exporting results: {e}")




def render_owner_detail_page():
    """Render the owner detail page with team hierarchy."""
    team = st.session_state.selected_team_for_detail

    if team is None:
        st.error("No team selected")
        if st.button("← Back to Auction"):
            st.session_state.current_view = "auction"
            st.rerun()
        return

    # Back button at the top
    if st.button("← Back to Auction", key="back_top"):
        st.session_state.current_view = "auction"
        st.rerun()

    st.title(f"🏏 {team.name}")

    # Display team logo if available
    logo_img = load_team_logo(team.logo_filename)
    if logo_img:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(logo_img, width=200)

    st.divider()

    # Find owner in players
    owner = None
    regular_players = []
    for player in team.players:
        if player.primary_role == "Team Owner":
            owner = player
        else:
            regular_players.append(player)

    # Display owner details
    if owner:
        st.header("👨‍💼 Team Owner")

        col1, col2 = st.columns([1, 2])

        with col1:
            # Display owner photo
            owner_img = load_player_image(owner.photo_filename)
            st.image(owner_img, width=250)

        with col2:
            st.markdown(f"""
            ### {owner.full_name}

            **Contact:** {owner.contact_number}

            **Role:** {owner.primary_role}

            **Batting Hand:** {owner.batting_hand}

            **Bowling Hand:** {owner.bowling_hand}

            **Connection:** {owner.connection}
            """)

    st.divider()

    # Display team hierarchy
    st.header("📊 Team Hierarchy")

    # Team statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Players", len(team.players))
    with col2:
        st.metric("Budget Remaining", f"₹{team.remaining_budget:,}")
    with col3:
        st.metric("Total Spent", f"₹{team.get_total_spent():,}")

    st.divider()

    # Display players in a tree/grid format with photos
    if regular_players:
        st.subheader(f"Team Squad ({len(regular_players)} Players)")

        # Display players in a grid (3 columns)
        for i in range(0, len(regular_players), 3):
            cols = st.columns(3)
            for j, col in enumerate(cols):
                if i + j < len(regular_players):
                    player = regular_players[i + j]
                    with col:
                        # Player card with photo
                        player_img = load_player_image(player.photo_filename)
                        st.image(player_img, use_container_width=True)

                        st.markdown(f"""
                        <div style='
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            padding: 10px;
                            border-radius: 10px;
                            text-align: center;
                            color: white;
                            margin-bottom: 20px;
                        '>
                            <h4 style='margin: 5px 0; font-size: 16px;'>{player.full_name}</h4>
                            <p style='margin: 3px 0; font-size: 12px;'>{player.primary_role}</p>
                            <p style='margin: 3px 0; font-size: 12px;'>
                                🏏 {player.batting_hand} | 🎯 {player.bowling_hand}
                            </p>
                            <p style='margin: 3px 0; font-size: 14px; font-weight: bold;'>
                                ₹{player.sold_price:,}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
    else:
        st.info("No players in squad yet")

    st.divider()

    # Back button at the bottom
    if st.button("← Back to Auction", key="back_bottom"):
        st.session_state.current_view = "auction"
        st.rerun()


def main():
    """Main application function."""
    # Initialize session state
    initialize_session_state()

    # Check current view and route accordingly
    if st.session_state.current_view == "owner_detail":
        render_owner_detail_page()
        return

    # Render title
    st.title(f"🏏 {LEAGUE_NAME}")
    if LEAGUE_SEASON:
        st.markdown(f"##### {LEAGUE_SEASON}")

    # Render sidebar with teams
    render_sidebar()

    # Render auction statistics
    render_auction_stats()

    st.divider()

    # Check if auction is complete
    auction_manager = st.session_state.auction_manager
    if auction_manager.state.is_auction_complete:
        st.success("🎉 Auction Complete! All players have been auctioned.")

        # Check team completion
        incomplete_teams = []
        for team in auction_manager.teams:
            is_complete, msg = auction_manager.validate_team_completion(team)
            if not is_complete:
                incomplete_teams.append((team, msg))

        if incomplete_teams:
            st.warning("⚠️ Some teams don't have the required number of players!")
            for team, msg in incomplete_teams:
                st.error(msg)

        if st.button("Start New Auction"):
            auction_manager.reset_auction()
            st.rerun()

        # Show final results
        st.subheader("Final Team Rosters")
        teams_summary = auction_manager.get_teams_summary()

        for team_summary in teams_summary:
            with st.expander(
                f"{team_summary['name']} - {team_summary['player_count']}/{REQUIRED_PLAYERS_PER_TEAM} players"
            ):
                if team_summary["players"]:
                    for player in team_summary["players"]:
                        st.markdown(
                            f"- **{player.full_name}** ({player.primary_role}) - ₹{player.sold_price:,}"
                        )
                else:
                    st.info("No players in this team")

        return

    # Render current player
    render_current_player()

    st.divider()

    # Render bidding controls
    render_bidding_controls()

    # Render navigation
    render_navigation()


if __name__ == "__main__":
    main()

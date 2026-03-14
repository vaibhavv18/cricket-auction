# 🏏 Cricket Auction Management System

A local cricket tournament auction app built with Python and Streamlit. Run live player auctions with real-time budget tracking, player photos, team management, and multi-round support for unsold players.

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-1.31+-red)

---

## Features

- **Live Auction Board** — Random player selection with animation, photo display, and role details
- **Budget Tracking** — Real-time remaining budget per team, with warnings when funds run low
- **Multi-Round Support** — Unsold players automatically roll into the next round
- **Team Owner Pages** — Click any owner to see their full squad with photos and stats
- **Budget Recovery** — If a team can't complete their squad, sell back their highest player at 50% refund
- **Player Order Exceptions** — Pin specific players to auction positions via JSON config
- **Export Results** — Save rosters and auction results as CSV

---

## Project Structure

```
Auction/
├── app.py                      # Main Streamlit application
├── auction_logic.py            # Auction business logic
├── data_manager.py             # CSV loading and data exports
├── models.py                   # Data models (Player, Team, AuctionState)
├── config.py                   # App configuration (reads from data/settings.json)
├── utils.py                    # Helper tools (photo check, rename, placeholders)
├── requirements.txt
├── run.sh                      # Quick start script (macOS/Linux)
├── run.bat                     # Quick start script (Windows)
├── data/
│   ├── settings.json           # League name, season, CSV column config
│   ├── config.json             # Teams, owners, budgets, logos
│   ├── player.csv              # Player registrations (not tracked in git)
│   └── player_order_exceptions.json  # Optional: fix players to auction positions
└── images/
    ├── *.png                   # Team logos (tracked)
    └── *.jpg / *.jpeg          # Player photos (not tracked in git)
```

---

## Quick Start

### First Run

```bash
./run.sh
```

This sets up the virtual environment and installs dependencies automatically. The app opens at `http://localhost:8501`.

### Manual Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

---

## Configuration

### 1. League Settings — `data/settings.json`

Change the league name, season, and Google Form question text here:

```json
{
  "league_name": "My Cricket League",
  "season": "Season 2026",
  "connection_question": "What is your connection to the league?"
}
```

### 2. Teams — `data/config.json`

Add your teams, owners, budgets, and optional logo filenames:

```json
[
  {
    "name": "Team Lions",
    "owner": "Owner Name",
    "budget": 50000,
    "logo": "team_lions.png"
  }
]
```

Place logo images (`.png`) in the `images/` folder.

### 3. Players — `data/player.csv`

Export your Google Form registrations as CSV. The app expects these column headers:

| Column | Header |
|--------|--------|
| Timestamp | `Timestamp` |
| Full Name | `Full Name` |
| Contact | `Contact Number (WhatsApp preferred)` |
| Batting Hand | `Select your batting hand and bowling arm [Batting Hand]` |
| Bowling Hand | `Select your batting hand and bowling arm [Bowling Hand]` |
| Role | `What is your primary role on the pitch?` |
| Connection | *(configured in `settings.json` → `connection_question`)* |

### 4. Player Photos

Name photos after the player: `firstname_lastname.jpg` (lowercase, underscores).

Example: `Vaibhav Ahir` → `vaibhav_ahir.jpg`

Place them in the `images/` folder. Missing photos show a placeholder.

**Check which photos are missing:**
```bash
python utils.py
```

### 5. Player Order Exceptions — `data/player_order_exceptions.json`

To fix a specific player at a specific auction position:

```json
{
  "Vaibhav Ahir": 1
}
```

Leave the file as `{}` to use fully random order.

---

## Auction Workflow

1. Click **Next Player** — random selection animation picks a player
2. View the player's photo, role, batting/bowling style
3. Select a team and enter bid amount (minimum ₹500)
4. Click **SOLD** or **UNSOLD**
5. Repeat until all players are auctioned
6. Unsold players come back in the next round
7. **Export** results when done

### Budget Recovery

If a team runs out of budget before filling their 14-player squad, a warning appears in the sidebar. You can sell back their most expensive player — the team gets a **50% refund** and the player re-enters the auction pool.

---

## Troubleshooting

**App takes long to start** — Use `run.sh` instead of `run_fixed.sh`. The new script reuses the existing virtual environment instead of rebuilding it every time.

**Player photos not showing** — Run `python utils.py` → option 2 to check missing photos.

**CSV import error** — Make sure column headers match exactly. Check `data/settings.json` for the `connection_question` value.

**Owner not detected** — The app matches owner names from `data/config.json` against `data/player.csv` using partial name matching. Make sure the owner's name in config appears in the CSV.

---

## License

MIT — free to use, modify, and distribute.

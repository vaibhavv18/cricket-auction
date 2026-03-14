# Cricket Auction Management System

A local cricket tournament auction app built with Python and Streamlit. Handles live player auctions with real-time budget tracking, photo display, multi-round unsold player support, and team owner management.

---

## Requirements

- Python 3.10 or higher
- pip

---

## Setup

Clone the repo and set up a virtual environment:

```bash
git clone https://github.com/YOUR_USERNAME/cricket-auction.git
cd cricket-auction

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Run the app:

```bash
streamlit run app.py
```

The app opens at http://localhost:8501.

---

## Project Structure

```
.
├── app.py                      # Streamlit UI
├── auction_logic.py            # Auction engine
├── data_manager.py             # CSV loading and result exports
├── models.py                   # Player, Team, AuctionState dataclasses
├── config.py                   # Constants, loads from data/settings.json
├── utils.py                    # CLI tools for managing player photos
├── requirements.txt
├── tests/
│   ├── test_models.py
│   ├── test_auction_logic.py
│   └── test_data_manager.py
├── data/
│   ├── settings.json           # League name, season, form question text
│   ├── config.json             # Teams, owners, budgets, logos
│   └── player_order_exceptions.json
└── images/
    └── *.png                   # Team logos (player photos are gitignored)
```

---

## Configuration

### League name and season — `data/settings.json`

```json
{
  "league_name": "My Cricket League",
  "season": "Season 2026",
  "connection_question": "What is your connection to the league?"
}
```

The `connection_question` value must match the exact column header in your player CSV (this comes from your Google Form).

### Teams — `data/config.json`

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

Place team logo images in the `images/` folder. The `logo` field is optional.

### Players — `data/player.csv`

Export your Google Form responses as CSV. Expected column headers:

- `Timestamp`
- `Full Name`
- `Contact Number (WhatsApp preferred)`
- `Select your batting hand and bowling arm [Batting Hand]`
- `Select your batting hand and bowling arm [Bowling Hand]`
- `What is your primary role on the pitch?`
- *(connection question — configured in settings.json)*

This file is gitignored since it contains personal contact information.

### Player photos

Name photos `firstname_lastname.jpg` (lowercase, underscores) and drop them in `images/`. Photos are also gitignored.

To check which photos are missing:

```bash
python utils.py
```

### Player order exceptions — `data/player_order_exceptions.json`

To force a specific player to a specific auction position:

```json
{
  "Player Name": 1
}
```

Leave it as `{}` for fully random order.

---

## How the auction works

1. Click **Next Player** — a brief animation runs, then one player is selected randomly
2. The player's photo, role, and batting/bowling details are shown
3. Select a team and enter a bid amount (minimum Rs.500)
4. Click **SOLD** to assign, or **UNSOLD** to skip
5. Unsold players come back in the next round automatically
6. If a team runs out of budget before filling their squad, a warning appears in the sidebar — you can sell back their most expensive player for a 50% refund
7. When all players are done, use the **Export** button to save results as CSV

Team owners are loaded from the player CSV and automatically placed in their teams — they do not go through the auction.

---

## Running tests

```bash
pip install pytest
pytest tests/
```

---

## Troubleshooting

**App is slow to start** — the virtual environment is probably being rebuilt. Make sure you activate it first before running.

**CSV import fails** — check that your column headers match exactly. The connection question header must match what's in `data/settings.json`.

**Owner not detected** — the app matches owner names from `config.json` against the player CSV using partial name matching. Make sure the owner's name appears somewhere in the CSV full name field.

**Player photo not showing** — run `python utils.py` and check option 2 to see which photos are missing.

---

## License

MIT

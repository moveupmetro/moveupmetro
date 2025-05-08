
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit
import json, copy, random, os
from supabase import upsert_profile, fetch_profiles, upsert_leaderboard, fetch_leaderboard

app = Flask(__name__)
app.secret_key = 'cloud-save'
socketio = SocketIO(app)

with open("static/card_decks.json") as f:
    RAW_DECKS = json.load(f)

def init_deck_state():
    return {
        name: {
            "draw_pile": copy.deepcopy(cards),
            "discard_pile": []
        } for name, cards in RAW_DECKS.items()
    }

position_map = {
    "Metro Entrance": (1000, 750),
    "Paycheck": (1080, 750),
    "Opportunity": (1160, 750),
    "First Job": (1240, 750),
    "Side Hustle": (1240, 670),
    "Twist": (1320, 670),
    "Marketplace": (1400, 670),
    "Economic Shift": (1480, 670),
    "Lifestyle Goal": (1560, 670),
    "Skill Building": (1320, 590),
    "Job Leads": (1240, 590),
    "Risten Launch": (1400, 750),
    "Startup Launched 1": (1480, 750),
    "Startup Launched 2": (1560, 750),
    "GOAL": (1640, 670),
    "Event 1": (1080, 670),
    "Event 2": (1160, 670),
    "Boost 1": (1400, 590),
    "Boost 2": (1480, 590),
    "Promotion": (1320, 830),
    "Freelance Gig": (1240, 830),
    "Debt": (1160, 830),
    "Financial Aid": (1080, 830),
    "Networking Event": (1000, 830),
    "Certification": (1400, 510),
    "Mentorship": (1480, 510),
    "Fail Forward": (1560, 510),
    "Rebrand": (1640, 510),
    "Side Pivot": (1480, 830),
    "Crowdfunding": (1400, 830),
    "Market Crash": (1320, 910),
    "Grant Award": (1240, 910),
    "Internship": (1160, 910),
    "Promotion 2": (1480, 910),
    "Lifestyle Reset": (1560, 910),
    "Startup Reboot": (1640, 910),
    "Pivot Again": (1720, 830),
    "Final Hustle": (1800, 750),
    "End Game": (1880, 750),
    "Legacy Choice": (1960, 670),
    "Mastery Track": (2040, 590),
    "Victory Loop": (2040, 510),
    "Encore Goal": (2040, 430),
    "Double Down": (1960, 350),
    "Burnout": (1880, 350),
    "Recovery": (1800, 350),
    "Renewal": (1720, 350),
    "Final Mentor": (1640, 350),
    "Graduation": (1560, 350),
}


edges = [
    ("Metro Entrance", "Paycheck"), ("Paycheck", "Opportunity"),
    ("Opportunity", "First Job"), ("First Job", "Lifestyle Goal")
]

GAME = {
    "players": [],
    "turn_index": 0,
    "log": [],
    "last_card": None,
    "decks": init_deck_state()
}

LEADERBOARD = []
PROFILES = {}

def update_profile(player):
    # badge logic
    player.setdefault("badges", [])
    if player["money"] >= 1000 and "Wealthy" not in player["badges"]:
        player["badges"].append("Wealthy")
        GAME["log"].append(f"🏅 {player['name']} earned badge Wealthy")
    if len(player["inventory"]) >= 5 and "Collector" not in player["badges"]:
        player["badges"].append("Collector")
        GAME["log"].append(f"🏅 {player['name']} earned badge Collector")

    profile = {
        "name": player["name"],
        "games_played": 1,
        "wins": 1 if player.get("has_won") else 0,
        "money_earned": player["money"],
        "cards_collected": len(player["inventory"])
    }
    upsert_profile(profile)

def update_leaderboard():
    entries = []
    for player in GAME["players"]:
        if player.get("has_won"):
            entries.append({
                "name": player["name"],
                "money": player["money"],
                "cards": len(player["inventory"]),
                "badges": len(player.get("badges", []))
            })
            update_profile(player)
    if entries:
        upsert_leaderboard(entries)

@app.route("/profiles")
def profiles():
    return render_template("profiles.html", profiles={p["name"]: p for p in fetch_profiles()})

@app.route("/leaderboard")
def leaderboard():
    return render_template("leaderboard.html", entries=fetch_leaderboard())

@app.route("/")
def home():
    return render_template("realtime.html")

@socketio.on("join")
def handle_join(data):
    name = data.get("name")
    if name and name not in [p["name"] for p in GAME["players"]]:
        GAME["players"].append({
            "name": name,
            "position": "Metro Entrance",
            "money": 0,
            "inventory": [],
            "has_won": False
        })
    session["player_name"] = name
    emit("update", GAME, broadcast=True)

@socketio.on("take_turn")
def handle_turn():
    name = session.get("player_name")
    player = GAME["players"][GAME["turn_index"]]
    if player["name"] != name:
        GAME["log"].append(f"⚠️ {name} tried to act out of turn.")
        emit("update", GAME, broadcast=True)
        return

    if player.get("skip_next_turn"):
        GAME["log"].append(f"⏭️ {name} skipped turn.")
        player["skip_next_turn"] = False
        GAME["last_card"] = None
    else:
        pos = player["position"]
        next_stops = [t for (f, t) in edges if f == pos]
        if next_stops:
            next_stop = next_stops[0]
            player["position"] = next_stop
            GAME["log"].append(f"{name} moved to {next_stop}")
            if next_stop == "Opportunity":
                GAME["log"].append(draw_and_apply_card("opportunity", player))
            elif next_stop == "First Job":
                player["money"] += 1000
                GAME["log"].append(f"{name} earned $1000.")
                GAME["last_card"] = None
            elif "Goal" in next_stop:
                player["has_won"] = True
                GAME["log"].append(f"🎯 {name} reached the goal!")
                GAME["last_card"] = None
                update_leaderboard()

    if not player.get("extra_turn"):
        GAME["turn_index"] = (GAME["turn_index"] + 1) % len(GAME["players"])
    else:
        player["extra_turn"] = False
        GAME["log"].append(f"🔁 {name} takes another turn.")

    emit("update", GAME, broadcast=True)

@socketio.on("reset")
def handle_reset():
    GAME["players"] = []
    GAME["turn_index"] = 0
    GAME["log"] = []
    GAME["last_card"] = None
    GAME["decks"] = init_deck_state()
    session.clear()
    emit("update", GAME, broadcast=True)

def draw_card(deck_name):
    deck = GAME["decks"][deck_name]
    if not deck["draw_pile"]:
        deck["draw_pile"] = deck["discard_pile"]
        deck["discard_pile"] = []
        random.shuffle(deck["draw_pile"])
        GAME["log"].append("🔄 {} deck reshuffled.".format(deck_name.capitalize()))
    if not deck["draw_pile"]:
        return None
    card = deck["draw_pile"].pop()
    deck["discard_pile"].append(card)
    return card

def draw_and_apply_card(deck_name, player):
    card = draw_card(deck_name)
    if not card:
        return f"{deck_name} deck is empty!"
    player['inventory'].append(card["name"])
    GAME["last_card"] = card
    msg = f"🃏 {player['name']} drew {card['name']}"
    effect = card.get("effect", {})

    if "money" in effect:
        player["money"] += effect["money"]
        msg += f" and {'gained' if effect['money'] > 0 else 'lost'} ${abs(effect['money'])}"
    if "badge" in effect:
        player.setdefault("badges", []).append(effect["badge"])
        msg += f" and earned badge '{effect['badge']}'"
    if "lose_random_card" in effect and player["inventory"]:
        lost = random.choice(player["inventory"])
        player["inventory"].remove(lost)
        msg += f" and lost card '{lost}'"
    if "skip_next_turn" in effect:
        player["skip_next_turn"] = True
        msg += " and will skip next turn"
    if "extra_turn" in effect:
        player["extra_turn"] = True
        msg += " and gets an extra turn"

    return msg

if __name__ == "__main__":
    socketio.run(app, debug=True)


@app.route("/editor", methods=["GET", "POST"])
def editor():
    path = "static/card_decks.json"
    if request.method == "POST":
        try:
            with open(path, "w") as f:
                json.dump(json.loads(request.form["data"]), f, indent=2)
        except Exception as e:
            return f"<pre>❌ Error: {e}</pre><a href='/editor'>Back</a>"
    with open(path) as f:
        decks = json.load(f)
    return render_template("editor.html", decks_json=json.dumps(decks, indent=2))


@app.route("/unlock", methods=["GET", "POST"])
def unlock():
    code = request.form.get("code") if request.method == "POST" else None
    valid_codes = {"PREMIUM2025": "career_premium", "ADVANTAGE2025": "financial_advantage"}
    unlocked = session.get("unlocked", [])
    msg = ""
    if code:
        if code in valid_codes and valid_codes[code] not in unlocked:
            unlocked.append(valid_codes[code])
            session["unlocked"] = unlocked
            msg = f"✅ Unlocked: {valid_codes[code]}"
        else:
            msg = "❌ Invalid or already used code."
    return render_template("unlock.html", msg=msg)

import urllib.request
import json
from pathlib import Path
from datetime import datetime, timezone

CAPITAL = 100.0
FEE = 0.004
COINS = ["XBTEUR", "ETHEUR", "SOLEUR",
         "XRPEUR", "ADAEUR", "LINKEUR",
         "DOTEUR", "AVAXEUR", "DOGEEUR",
         "SUIEUR"]

FILE = Path("portfolio.json")

if FILE.exists():
    state = json.loads(FILE.read_text())
else:
    state = {
        "cash": CAPITAL,
        "positions": {},
        "history": []
    }

def market(pair):
    url = (
        "https://api.kraken.com/0/public/OHLC"
        f"?pair={pair}&interval=15"
    )
    with urllib.request.urlopen(url, timeout=20) as r:
        data = json.load(r)
    if data["error"]:
        raise ValueError(data["error"])
    result = data["result"]
    key = next(k for k in result if k != "last")
    return [float(c[4]) for c in result[key][:-1]]

def record(action, pair, price):
    state["history"].append({
        "date": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "crypto": pair,
        "price": price
    })

prices = {}

for pair in COINS:
    try:
        closes = market(pair)
        if len(closes) < 30:
            continue

        price = closes[-1]
        prices[pair] = price
        fast = sum(closes[-7:]) / 7
        slow = sum(closes[-25:]) / 25

        position = state["positions"].get(pair)

        if position:
            change = price / position["entry"] - 1
            if change <= -0.03 or change >= 0.06 or fast < slow:
                value = position["quantity"] * price
                state["cash"] += value * (1 - FEE)
                del state["positions"][pair]
                record("VENTE", pair, price)

        elif (
            fast > slow
            and price > fast
            and len(state["positions"]) < 3
            and state["cash"] >= 20
        ):
            amount = 20
            state["cash"] -= amount
            state["positions"][pair] = {
                "entry": price,
                "quantity": amount * (1 - FEE) / price
            }
            record("ACHAT", pair, price)

        print(pair, price, "EUR")

    except Exception as e:
        print(pair, "Erreur :", e)

total = state["cash"]

for pair, position in state["positions"].items():
    total += position["quantity"] * prices.get(
        pair, position["entry"]
    )

state["estimated_value"] = round(total, 2)
state["profit"] = round(total - CAPITAL, 2)
state["updated"] = datetime.now(timezone.utc).isoformat()

FILE.write_text(
    json.dumps(state, indent=2),
    encoding="utf-8"
)

print("Capital virtuel :", round(total, 2), "EUR")
print("Benefice/perte :", state["profit"], "EUR")
print("SIMULATION UNIQUEMENT")

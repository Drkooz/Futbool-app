import requests
import pandas as pd
from datetime import datetime, timedelta

from config import API_KEY, LIGAS
from model import team_strength, match_probabilities
from utils import market_odds, edge

# =========================
# HEADERS
# =========================
HEADERS = {"9ac6384534674eb593649352a93a2afc": API_KEY}

# =========================
# FECHAS
# =========================
hoy = datetime.now().date()
fecha_fin = hoy + timedelta(days=4)

# =========================
# FETCH MATCHES
# =========================
all_matches = []

for liga, lid in LIGAS.items():

    url = f"https://api.football-data.org/v4/competitions/{lid}/matches"

    params = {
        "dateFrom": str(hoy),
        "dateTo": str(fecha_fin)
    }

    try:
        res = requests.get(url, headers=HEADERS, params=params, timeout=10).json()

        for m in res.get("matches", []):
            m["liga"] = liga
            all_matches.append(m)

    except:
        continue

print("⚽ PARTIDOS TOTALES:", len(all_matches))

# =========================
# ENGINE
# =========================
portfolio = []

for m in all_matches:

    try:
        home_id = m["homeTeam"]["id"]
        away_id = m["awayTeam"]["id"]

        home_strength = team_strength(home_id, HEADERS)
        away_strength = team_strength(away_id, HEADERS)

        ph, pd, pa = match_probabilities(home_strength, away_strength)

        bets = {
            m["homeTeam"]["name"]: ph,
            "EMPATE": pd,
            m["awayTeam"]["name"]: pa
        }

        for name, prob in bets.items():

            odds = market_odds(prob)
            e = edge(prob, odds)

            # filtro estable (CLAVE)
            if e < 0.02:
                continue

            kelly = (prob * odds - 1) / (odds - 1)
            kelly = max(0, min(kelly * 0.5, 0.05))

            score = prob * e

            portfolio.append({
                "LIGA": m["liga"],
                "PARTIDO": f'{m["homeTeam"]["name"]} vs {m["awayTeam"]["name"]}',
                "BET": name,
                "PROB": round(prob * 100, 2),
                "EDGE": round(e * 100, 2),
                "ODDS": round(odds, 2),
                "SCORE": round(score, 4),
                "KELLY": round(kelly * 100, 2)
            })

    except:
        continue

# =========================
# OUTPUT STABLE TOP 5
# =========================
df = pd.DataFrame(portfolio)

if df.empty:
    print("\n⚠️ NO HAY PICKS (EDGE INSUFICIENTE O MODELO CONSERVADOR)")
else:

    df = df.sort_values("SCORE", ascending=False).head(5)

    print("\n💼🔥 HEDGE FUND QUANT — FINAL STABLE TOP 5\n")

    exposure = 0

    for _, r in df.iterrows():

        exposure += r["KELLY"]

        print("=" * 70)
        print(f"🏆 {r['LIGA']}")
        print(f"⚽ {r['PARTIDO']}")
        print(f"💰 BET: {r['BET']}")
        print(f"📊 PROB: {r['PROB']}% | EDGE: {r['EDGE']}%")
        print(f"💵 KELLY: {r['KELLY']}%")
        print("=" * 70)

    print("\n📊 EXPOSICIÓN TOTAL:", round(exposure, 2), "%")
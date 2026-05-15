import requests
import numpy as np
from utils import poisson

# =========================
# TEAM STRENGTH MODEL
# =========================
def team_strength(team_id, headers):
    """
    Calcula fuerza ofensiva y defensiva basada en últimos partidos.
    """

    try:
        url = f"https://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED"
        r = requests.get(url, headers=headers, timeout=10).json()

        matches = r.get("matches", [])[-8:]

        # fallback seguro
        if len(matches) == 0:
            return {"atk": 1.2, "def": 1.2}

        gf = []
        gc = []

        for m in matches:
            home = m["homeTeam"]["id"] == team_id

            g_for = m["score"]["fullTime"]["home"] if home else m["score"]["fullTime"]["away"]
            g_against = m["score"]["fullTime"]["away"] if home else m["score"]["fullTime"]["home"]

            gf.append(g_for or 0)
            gc.append(g_against or 0)

        return {
            "atk": np.mean(gf),
            "def": np.mean(gc)
        }

    except:
        return {"atk": 1.2, "def": 1.2}


# =========================
# MATCH PROBABILITY ENGINE
# =========================
def match_probabilities(home_strength, away_strength, max_goals=5):
    """
    Genera probabilidades 1X2 usando Poisson.
    """

    lam_h = (home_strength["atk"] + away_strength["def"]) / 2
    lam_a = (away_strength["atk"] + home_strength["def"]) / 2

    home_win = 0
    draw = 0
    away_win = 0

    for i in range(max_goals):
        for j in range(max_goals):

            p = poisson(i, lam_h) * poisson(j, lam_a)

            if i > j:
                home_win += p
            elif i == j:
                draw += p
            else:
                away_win += p

    total = home_win + draw + away_win

    if total == 0:
        return 0.33, 0.34, 0.33

    return (
        home_win / total,
        draw / total,
        away_win / total
    )
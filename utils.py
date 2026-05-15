import math
import random

# =========================
# POISSON DISTRIBUTION
# =========================
def poisson(k, lam):
    if lam <= 0:
        return 0
    return (lam ** k * math.exp(-lam)) / math.factorial(k)

# =========================
# MARKET ODDS SIMULATION
# =========================
def market_odds(prob):
    """
    Simula mercado con ruido realista.
    Convierte probabilidad → cuota.
    """
    noise = random.uniform(-0.07, 0.07)
    p = prob + noise

    # clamp seguridad
    p = max(0.01, min(0.99, p))

    return 1 / p

# =========================
# EDGE CALCULATION
# =========================
def edge(prob, odds):
    """
    Valor esperado del bet:
    > 0 = value bet
    < 0 = basura del mercado
    """
    return (prob * odds) - 1
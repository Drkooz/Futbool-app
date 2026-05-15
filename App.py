import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# ==========================================
# CONFIGURACIÓN GENERAL
# ==========================================

st.set_page_config(
    page_title="Elite Predictor Pro",
    page_icon="⚽",
    layout="wide"
)

# ==========================================
# CSS
# ==========================================

st.markdown("""
<style>

/* Fondo */
.stApp {
    background-color: #000000;
    background-image:
    linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)),
    url("https://images.unsplash.com/photo-1508098682722-e99c43a406b2?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80");
    background-size: cover;
}

/* Contenedor */
.block-container {
    background: rgba(20,20,20,0.95);
    border: 3px solid #39FF14;
    border-radius: 20px;
    padding: 30px;
    box-shadow: 0 0 40px rgba(57,255,20,0.3);
}

/* Textos */
h1, h2, h3, h4, p, span, li {
    color: white !important;
    font-weight: bold;
}

/* Select */
div[data-baseweb="select"] > div {
    background-color: white !important;
    border: 2px solid #39FF14 !important;
}

div[data-baseweb="select"] span {
    color: black !important;
}

/* Botón */
.stButton > button {
    background: #39FF14 !important;
    color: black !important;
    font-size: 20px !important;
    font-weight: bold !important;
    border-radius: 50px !important;
    height: 3em !important;
    width: 100% !important;
}

/* Métricas */
div[data-testid="stMetric"] {
    background: #111111;
    border: 2px solid #39FF14;
    border-radius: 15px;
    padding: 20px;
}

div[data-testid="stMetricValue"] {
    color: #39FF14 !important;
    font-size: 32px !important;
}

</style>
""", unsafe_allow_html=True)

# ==========================================
# LIGAS
# ==========================================

LIGAS_DICT = {
    "EUROPA - CHAMPIONS LEAGUE": 2001,
    "INGLATERRA - PREMIER LEAGUE": 2021,
    "ESPAÑA - LA LIGA": 2014,
    "ITALIA - SERIE A": 2019,
    "ALEMANIA - BUNDESLIGA": 2002,
    "FRANCIA - LIGUE 1": 2015
}

st.markdown("# ⚽ ELITE FOOTBALL SCANNER")
st.markdown("### PROFESSIONAL DATA ANALYSIS")

seleccion = st.selectbox(
    "📍 ELIGE TU LIGA:",
    list(LIGAS_DICT.keys())
)

liga_id = LIGAS_DICT[seleccion]

# ==========================================
# API
# ==========================================

API_KEY = "TU_API_KEY"
HEADERS = {'X-Auth-Token': API_KEY}

# ==========================================
# FUNCIÓN PRINCIPAL
# ==========================================

@st.cache_data(ttl=3600)
def obtener_fuerza(id_equipo):

    url = f"https://api.football-data.org/v4/teams/{id_equipo}/matches?status=FINISHED"

    try:
        res = requests.get(url, headers=HEADERS).json()

        partidos = res.get('matches', [])[-10:]

        if not partidos:
            return {
                'ataque': 1,
                'defensa': 1,
                'forma': 0.5,
                'over25': 0.5,
                'local_winrate': 0.5,
                'visit_winrate': 0.5,
                'dif_goles': 0
            }

        pesos = [1,2,3,4,5,6,7,8,9,10]

        goles_favor = 0
        goles_contra = 0
        puntos = 0
        over25 = 0
        dif_total = 0

        local_games = 0
        local_wins = 0

        away_games = 0
        away_wins = 0

        peso_total = sum(pesos)

        for i, m in enumerate(partidos):

            peso = pesos[i]

            es_local = m['homeTeam']['id'] == id_equipo

            gf = (
                m['score']['fullTime']['home']
                if es_local
                else m['score']['fullTime']['away']
            )

            gc = (
                m['score']['fullTime']['away']
                if es_local
                else m['score']['fullTime']['home']
            )

            gf = gf if gf is not None else 0
            gc = gc if gc is not None else 0

            goles_favor += gf * peso
            goles_contra += gc * peso

            dif_total += (gf - gc)

            # FORMA
            if gf > gc:

                puntos += 3 * peso

                if es_local:
                    local_wins += 1
                else:
                    away_wins += 1

            elif gf == gc:
                puntos += 1 * peso

            # OVER 2.5
            if (gf + gc) >= 3:
                over25 += peso

            # LOCAL / VISITA
            if es_local:
                local_games += 1
            else:
                away_games += 1

        ataque = goles_favor / peso_total
        defensa = goles_contra / peso_total

        forma = puntos / (peso_total * 3)

        over25_rate = over25 / peso_total

        local_winrate = (
            local_wins / local_games
            if local_games > 0 else 0.5
        )

        away_winrate = (
            away_wins / away_games
            if away_games > 0 else 0.5
        )

        return {
            'ataque': ataque,
            'defensa': defensa,
            'forma': forma,
            'over25': over25_rate,
            'local_winrate': local_winrate,
            'visit_winrate': away_winrate,
            'dif_goles': dif_total / len(partidos)
        }

    except:
        return {
            'ataque': 1,
            'defensa': 1,
            'forma': 0.5,
            'over25': 0.5,
            'local_winrate': 0.5,
            'visit_winrate': 0.5,
            'dif_goles': 0
        }

# ==========================================
# BOTÓN PRINCIPAL
# ==========================================

if st.button(f"🏟️ ANALIZAR {seleccion}"):

    hoy = datetime.now()

    consolidado = []

    with st.status("🚀 PROCESANDO DATOS...", expanded=True):

        try:

            url = f"https://api.football-data.org/v4/competitions/{liga_id}/matches"

            params = {
                'dateFrom': hoy.date(),
                'dateTo': (hoy + timedelta(days=5)).date()
            }

            data = requests.get(
                url,
                headers=HEADERS,
                params=params
            ).json()

            partidos = data.get('matches', [])

            if not partidos:

                st.warning("SIN PARTIDOS DISPONIBLES")

            else:

                for p in partidos[:6]:

                    st.write(
                        f"✔ Analizando: "
                        f"{p['homeTeam']['name']} vs "
                        f"{p['awayTeam']['name']}"
                    )

                    local = obtener_fuerza(
                        p['homeTeam']['id']
                    )

                    visita = obtener_fuerza(
                        p['awayTeam']['id']
                    )

                    # ==================================
                    # NUEVO MODELO
                    # ==================================

                    score_local = (
                        local['ataque'] * 0.30 +
                        (2 - visita['defensa']) * 0.20 +
                        local['forma'] * 0.20 +
                        local['local_winrate'] * 0.15 +
                        local['dif_goles'] * 0.10 +
                        local['over25'] * 0.05
                    )

                    score_visita = (
                        visita['ataque'] * 0.30 +
                        (2 - local['defensa']) * 0.20 +
                        visita['forma'] * 0.20 +
                        visita['visit_winrate'] * 0.15 +
                        visita['dif_goles'] * 0.10 +
                        visita['over25'] * 0.05
                    )

                    # ==================================
                    # EMPATE
                    # ==================================

                    diferencia = abs(
                        score_local - score_visita
                    )

                    prob_empate = max(
                        15,
                        35 - (diferencia * 10)
                    )

                    total = score_local + score_visita

                    prob_local = (
                        (score_local / total)
                        * (100 - prob_empate)
                    )

                    prob_visita = (
                        (score_visita / total)
                        * (100 - prob_empate)
                    )

                    # Limitar extremos
                    prob_local = max(5, min(prob_local, 90))
                    prob_visita = max(5, min(prob_visita, 90))

                    # FAVORITO
                    favorito = "EMPATE"

                    if prob_local > prob_visita and prob_local > prob_empate:
                        favorito = p['homeTeam']['name']

                    elif prob_visita > prob_local and prob_visita > prob_empate:
                        favorito = p['awayTeam']['name']

                    # FECHA
                    fecha_dt = datetime.strptime(
                        p['utcDate'],
                        "%Y-%m-%dT%H:%M:%SZ"
                    )

                    fecha_local = fecha_dt - timedelta(hours=5)

                    consolidado.append({

                        'FECHA':
                            fecha_local.strftime("%d %b | %H:%M"),

                        'LOCAL':
                            p['homeTeam']['name'],

                        'VISITA':
                            p['awayTeam']['name'],

                        'L %':
                            round(prob_local, 1),

                        'EMPATE %':
                            round(prob_empate, 1),

                        'V %':
                            round(prob_visita, 1),

                        'FAVORITO':
                            favorito,

                        'GOLES':
                            round(
                                local['ataque']
                                +
                                visita['ataque'],
                                2
                            )
                    })

        except Exception as e:
            st.error(f"ERROR: {e}")

    # ==========================================
    # RESULTADOS
    # ==========================================

    if consolidado:

        df = pd.DataFrame(consolidado)

        st.markdown("## 🏆 SELECCIONES VIP")

        idx_dorada = (
            df[['L %', 'V %', 'EMPATE %']]
            .max(axis=1)
            .idxmax()
        )

        best = df.iloc[idx_dorada]

        c1, c2 = st.columns(2)

        with c1:

            st.metric(
                "🏆 APUESTA DORADA",
                best['FAVORITO'],
                f"{max(best['L %'], best['V %'], best['EMPATE %'])}%"
            )

            st.markdown(
                f"### {best['LOCAL']} vs {best['VISITA']}"
            )

            st.markdown(
                f"🕒 {best['FECHA']}"
            )

        with c2:

            heavy = df.loc[df['GOLES'].idxmax()]

            st.metric(
                "💀 OVER PROBABLE",
                f"{heavy['GOLES']} GOLES",
                "OVER 2.5"
            )

            st.markdown(
                f"### {heavy['LOCAL']} vs {heavy['VISITA']}"
            )

            st.markdown(
                f"🕒 {heavy['FECHA']}"
            )

        # ======================================
        # TABLA
        # ======================================

        st.markdown("## 📊 CALENDARIO COMPLETO")

        st.dataframe(
            df[
                [
                    'FECHA',
                    'LOCAL',
                    'VISITA',
                    'L %',
                    'EMPATE %',
                    'V %',
                    'FAVORITO'
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

import streamlit as st
import requests
import pandas as pd
import time
import random
from datetime import date, timedelta

# 1. CONFIGURACIÓN VISUAL
st.set_page_config(page_title="Elite Predictor", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    div[data-testid="stMetricValue"] { font-size: 26px; color: #00ffcc; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #1a73e8; color: white; height: 3.5em; font-weight: bold; }
    .stSelectbox label { color: #00ffcc !important; font-size: 18px; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ Elite Football Scanner v4.0")

# --- DICCIONARIO DE LIGAS ---
LIGAS_DICT = {
    "🇪🇺 Champions League": 2001,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": 2021,
    "🇪🇸 La Liga": 2014,
    "🇮🇹 Serie A": 2019,
    "🇩🇪 Bundesliga": 2002,
    "🇫🇷 Ligue 1": 2015
}

# --- SELECTOR DE LIGA EN LA INTERFAZ ---
seleccion = st.selectbox("🎯 Elige la liga que quieres analizar:", list(LIGAS_DICT.keys()))
liga_id = LIGAS_DICT[seleccion]

# --- DATOS DE CONEXIÓN ---
API_KEY = "9ac6384534674eb593649352a93a2afc"
HEADERS = { 'X-Auth-Token': API_KEY }

MENSAJES_ESPERA = [
    "⚽ Inflando los balones...", "🖥️ Consultando al VAR...", 
    "🏃 Los jugadores están calentando...", "🏟️ Regando el césped...",
    "📋 Analizando tácticas...", "👟 Lustrando los botines...",
    "⏳ Calculando probabilidades de último minuto..."
]

def obtener_fuerza(id_equipo):
    url = f"https://api.football-data.org/v4/teams/{id_equipo}/matches?status=FINISHED"
    try:
        time.sleep(11) # Respeto a la API gratuita
        res = requests.get(url, headers=HEADERS).json()
        p = res.get('matches', [])[-5:]
        if not p: return 1.0, 1.0
        g_m = sum(m['score']['fullTime']['home'] if m['homeTeam']['id'] == id_equipo else m['score']['fullTime']['away'] for m in p)
        g_r = sum(m['score']['fullTime']['away'] if m['homeTeam']['id'] == id_equipo else m['score']['fullTime']['home'] for m in p)
        return g_m/len(p), g_r/len(p)
    except: return 1.0, 1.0

# --- BOTÓN DE ESCANEO ---
if st.button(f'🚀 ANALIZAR {seleccion.upper()}'):
    hoy = date.today()
    consolidado = []
    
    with st.status(f"🔍 Analizando {seleccion}...", expanded=True) as status:
        try:
            url = f"https://api.football-data.org/v4/competitions/{liga_id}/matches"
            params = {'dateFrom': hoy, 'dateTo': hoy + timedelta(days=4)}
            data = requests.get(url, headers=HEADERS, params=params).json()
            partidos = data.get('matches', [])
            
            if not partidos:
                st.warning(f"No hay partidos próximos en {seleccion}.")
            else:
                # Limitamos a 4 partidos para que no tarde más de 1.5 minutos
                for p in partidos[:4]:
                    st.write(random.choice(MENSAJES_ESPERA))
                    l_nom, v_nom = p['homeTeam']['name'], p['awayTeam']['name']
                    of_l, df_l = obtener_fuerza(p['homeTeam']['id'])
                    of_v, df_v = obtener_fuerza(p['awayTeam']['id'])
                    
                    p_l = ((of_l + df_v) / 2) * 1.15
                    p_v = ((of_v + df_l) / 2) * 0.85
                    total = p_l + p_v
                    prob_l = (p_l / total) * 100 if total > 0 else 50
                    prob_v = (p_v / total) * 100 if total > 0 else 50
                    
                    consolidado.append({
                        'Local': l_nom,
                        'Visitante': v_nom,
                        'L %': round(prob_l, 1),
                        'V %': round(prob_v, 1),
                        'Goles': total,
                        'Favorito': l_nom if prob_l > prob_v else v_nom,
                        'Pick': 'Normal'
                    })
        except Exception as e:
            st.error(f"Error al conectar con la liga: {e}")
        
        status.update(label="✅ Análisis listo", state="complete", expanded=False)

    if consolidado:
        df = pd.DataFrame(consolidado)
        
        # Lógica de Medallas
        diffs = (df['L %'] - df['V %']).abs()
        df.loc[diffs.idxmax(), 'Pick'] = '🏆 DORADA'
        df.loc[df['Goles'].idxmax(), 'Pick'] = '💀 NEGRA'

        # TARJETAS DE RESULTADOS
        st.subheader(f"🌟 Destacados de {seleccion}")
        c1, c2 = st.columns(2)
        
        dorada = df[df['Pick'] == '🏆 DORADA'].iloc[0]
        with c1:
            st.metric("🏆 LA MEJOR OPCIÓN", dorada['Favorito'], f"{max(dorada['L %'], dorada['V %'])}% Prob.")
            st.caption(f"{dorada['Local']} vs {dorada['Visitante']}")

        negra = df[df['Pick'] == '💀 NEGRA'].iloc[0]
        with c2:
            st.metric("💀 LEY DEL EX / GOLES", "Más de 2.5", f"{round(negra['Goles'],1)} esperados")
            st.caption(f"{negra['Local']} vs {negra['Visitante']}")

        # TABLA SEPARADA POR EQUIPOS
        st.divider()
        st.subheader("📋 Todas las probabilidades")
        df_display = df[['Local', 'Visitante', 'L %', 'V %', 'Favorito']]
        # Añadir el símbolo de % para que se vea mejor
        df_display['L %'] = df_display['L %'].astype(str) + "%"
        df_display['V %'] = df_display['V %'].astype(str) + "%"
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("Pulsa el botón de arriba para ver los datos.")

import streamlit as st
import requests
import pandas as pd
import time
import random
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN VISUAL Y DISEÑO "ESTADIO"
st.set_page_config(page_title="Elite Predictor Pro", page_icon="⚽", layout="wide")

# CSS Avanzado para Fondo de Cancha, Bordes de Césped y Efecto Cristal
st.markdown("""
    <style>
    /* Fondo con imagen de estadio difuminada */
    .stApp {
        background-image: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)), 
        url("https://images.unsplash.com/photo-1508098682722-e99c43a406b2?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80");
        background-attachment: fixed;
        background-size: cover;
    }

    /* Borde "Césped" para el contenedor principal */
    .block-container {
        border: 4px solid #2e7d32;
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        padding: 20px !important;
        box-shadow: 0 0 20px rgba(46, 125, 50, 0.5);
    }

    /* Estilo de Tarjetas y Métricas */
    div[data-testid="stMetric"] {
        background: rgba(0, 0, 0, 0.4);
        border-radius: 15px;
        padding: 15px;
        border: 1px solid #00ffcc;
    }

    /* Títulos y Texto */
    h1, h2, h3, p {
        color: white !important;
        text-shadow: 2px 2px 4px #000000;
    }

    /* Botón Pro */
    .stButton>button {
        background: linear-gradient(90deg, #2e7d32, #1b5e20);
        color: white;
        border: none;
        font-weight: bold;
        border-radius: 30px;
        height: 3.5em;
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 15px #00ffcc;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DICCIONARIO DE LIGAS CON BANDERAS ---
LIGAS_DICT = {
    "🇪🇺 UEFA Champions League": 2001,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League (Inglaterra)": 2021,
    "🇪🇸 La Liga (España)": 2014,
    "🇮🇹 Serie A (Italia)": 2019,
    "🇩🇪 Bundesliga (Alemania)": 2002,
    "🇫🇷 Ligue 1 (Francia)": 2015
}

st.title("⚽ Scanner de Élite")
seleccion = st.selectbox("📍 Selecciona la competición:", list(LIGAS_DICT.keys()))
liga_id = LIGAS_DICT[seleccion]

API_KEY = "9ac6384534674eb593649352a93a2afc"
HEADERS = { 'X-Auth-Token': API_KEY }

def obtener_fuerza(id_equipo):
    url = f"https://api.football-data.org/v4/teams/{id_equipo}/matches?status=FINISHED"
    try:
        time.sleep(11) # Respeto a API gratuita
        res = requests.get(url, headers=HEADERS).json()
        p = res.get('matches', [])[-5:]
        if not p: return 1.0, 1.0
        g_m = sum(m['score']['fullTime']['home'] if m['homeTeam']['id'] == id_equipo else m['score']['fullTime']['away'] for m in p)
        g_r = sum(m['score']['fullTime']['away'] if m['homeTeam']['id'] == id_equipo else m['score']['fullTime']['home'] for m in p)
        return g_m/len(p), g_r/len(p)
    except: return 1.0, 1.0

if st.button(f'🏟️ ANALIZAR {seleccion.upper()}'):
    hoy = datetime.now()
    consolidado = []
    
    with st.status("📊 Procesando big data deportivo...", expanded=True) as status:
        try:
            url = f"https://api.football-data.org/v4/competitions/{liga_id}/matches"
            params = {'dateFrom': hoy.date(), 'dateTo': (hoy + timedelta(days=5)).date()}
            data = requests.get(url, headers=HEADERS, params=params).json()
            partidos = data.get('matches', [])
            
            if not partidos:
                st.warning(f"No hay partidos registrados hoy en {seleccion}.")
            else:
                for p in partidos[:4]:
                    st.write(f"🔄 Analizando: {p['homeTeam']['name']} vs {p['awayTeam']['name']}")
                    l_id, v_id = p['homeTeam']['id'], p['awayTeam']['id']
                    of_l, df_l = obtener_fuerza(l_id)
                    of_v, df_v = obtener_fuerza(v_id)
                    
                    # Cálculo de Predicción
                    p_l = ((of_l + df_v) / 2) * 1.15
                    p_v = ((of_v + df_l) / 2) * 0.85
                    total = p_l + p_v
                    prob_l = (p_l / total) * 100 if total > 0 else 50
                    
                    # Formatear Fecha
                    fecha_dt = datetime.strptime(p['utcDate'], "%Y-%m-%dT%H:%M:%SZ")
                    fecha_local = fecha_dt - timedelta(hours=5) # Ajuste manual a tu hora local
                    
                    consolidado.append({
                        'Fecha': fecha_local.strftime("%d %b - %H:%M"),
                        'Local': p['homeTeam']['name'],
                        'Visitante': p['awayTeam']['name'],
                        'L %': round(prob_l, 1),
                        'V %': round(100 - prob_l, 1),
                        'Favorito': p['homeTeam']['name'] if prob_l > 50 else p['awayTeam']['name'],
                        'Goles': total
                    })
        except: st.error("Error de conexión. Intenta en 1 minuto.")
        
        status.update(label="✅ Scanner Finalizado", state="complete", expanded=False)

    if consolidado:
        df = pd.DataFrame(consolidado)
        
        # --- TOP PICKS ---
        idx_dorada = (df['L %'] - 50).abs().idxmax()
        st.subheader(f"🌟 Los mejores Picks: {seleccion}")
        
        c1, c2 = st.columns(2)
        with c1:
            best = df.loc[idx_dorada]
            st.metric("🏆 APUESTA DORADA", best['Favorito'], f"{max(best['L %'], best['V %'])}%")
            st.write(f"📅 {best['Fecha']} | {best['Local']} vs {best['Visitante']}")
        
        with c2:
            heavy = df.loc[df['Goles'].idxmax()]
            st.metric("💀 APUESTA NEGRA", f"+{round(heavy['Goles'],1)} Goles", "Over 2.5")
            st.write(f"📅 {heavy['Fecha']} | {heavy['Local']} vs {heavy['Visitante']}")

        # --- TABLA DE DATOS ---
        st.divider()
        st.subheader("📋 Calendario Detallado")
        
        # Estilizar porcentajes para la tabla
        df_show = df[['Fecha', 'Local', 'Visitante', 'L %', 'V %', 'Favorito']]
        st.dataframe(df_show, use_container_width=True, hide_index=True)
        
        st.caption("⚠️ Los datos son estimaciones basadas en los últimos 5 encuentros oficiales.")

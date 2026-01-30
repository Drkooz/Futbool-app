import streamlit as st
import requests
import pandas as pd
import time
import random
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN VISUAL MAESTRA
st.set_page_config(page_title="Elite Predictor Pro", page_icon="⚽", layout="wide")

# CSS para inyectar estilo de "Estadio" y arreglar los emojis en PC
st.markdown("""
    <style>
    /* Fondo con imagen de estadio difuminada */
    .stApp {
        background-image: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), 
        url("https://images.unsplash.com/photo-1508098682722-e99c43a406b2?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80");
        background-attachment: fixed;
        background-size: cover;
    }

    /* Contenedor con borde de césped neón */
    .block-container {
        border: 3px solid #39FF14;
        border-radius: 25px;
        background: rgba(15, 15, 15, 0.85);
        backdrop-filter: blur(12px);
        padding: 30px !important;
        box-shadow: 0 0 30px rgba(57, 255, 20, 0.3);
        margin-top: 20px;
    }

    /* Truco para que los emojis brillen y se vean grandes en PC */
    .emoji {
        font-size: 24px;
        filter: drop-shadow(2px 2px 4px #000);
        margin-right: 10px;
    }

    /* Estilo de Tarjetas de Metricas */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid #39FF14;
        transition: 0.3s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        background: rgba(57, 255, 20, 0.1);
    }

    /* Botón con estilo deportivo */
    .stButton>button {
        background: linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%);
        color: white !important;
        border: 2px solid #39FF14;
        border-radius: 50px;
        height: 4em;
        font-weight: bold;
        font-size: 18px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
    }
    </style>
    """, unsafe_allow_html=True)

# Diccionario con banderas y nombres claros
LIGAS_DICT = {
    "🇪🇺 Champions League (Europa)": 2001,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League (Inglaterra)": 2021,
    "🇪🇸 La Liga (España)": 2014,
    "🇮🇹 Serie A (Italia)": 2019,
    "🇩🇪 Bundesliga (Alemania)": 2002,
    "🇫🇷 Ligue 1 (Francia)": 2015
}

st.markdown('<h1><span class="emoji">🚀</span>Elite Football Scanner</h1>', unsafe_allow_html=True)

seleccion = st.selectbox("📍 Selecciona tu Liga:", list(LIGAS_DICT.keys()))
liga_id = LIGAS_DICT[seleccion]

API_KEY = "9ac6384534674eb593649352a93a2afc"
HEADERS = { 'X-Auth-Token': API_KEY }

def obtener_fuerza(id_equipo):
    url = f"https://api.football-data.org/v4/teams/{id_equipo}/matches?status=FINISHED"
    try:
        time.sleep(11) 
        res = requests.get(url, headers=HEADERS).json()
        p = res.get('matches', [])[-5:]
        if not p: return 1.0, 1.0
        g_m = sum(m['score']['fullTime']['home'] if m['homeTeam']['id'] == id_equipo else m['score']['fullTime']['away'] for m in p)
        g_r = sum(m['score']['fullTime']['away'] if m['homeTeam']['id'] == id_equipo else m['score']['fullTime']['home'] for m in p)
        return g_m/len(p), g_r/len(p)
    except: return 1.0, 1.0

if st.button(f'🏟️ ANALIZAR COMPETICIÓN'):
    hoy = datetime.now()
    consolidado = []
    
    with st.status("📊 Escaneando bases de datos...", expanded=True) as status:
        try:
            url = f"https://api.football-data.org/v4/competitions/{liga_id}/matches"
            params = {'dateFrom': hoy.date(), 'dateTo': (hoy + timedelta(days=5)).date()}
            data = requests.get(url, headers=HEADERS, params=params).json()
            partidos = data.get('matches', [])
            
            if not partidos:
                st.warning("No hay partidos próximos.")
            else:
                for p in partidos[:4]:
                    st.write(f"🔎 Procesando: **{p['homeTeam']['name']} vs {p['awayTeam']['name']}**")
                    of_l, df_l = obtener_fuerza(p['homeTeam']['id'])
                    of_v, df_v = obtener_fuerza(p['awayTeam']['id'])
                    
                    p_l = ((of_l + df_v) / 2) * 1.15
                    p_v = ((of_v + df_l) / 2) * 0.85
                    total = p_l + p_v
                    prob_l = (p_l / total) * 100 if total > 0 else 50
                    
                    fecha_dt = datetime.strptime(p['utcDate'], "%Y-%m-%dT%H:%M:%SZ")
                    # Ajuste a tu zona horaria (Cúcuta es UTC-5)
                    fecha_local = fecha_dt - timedelta(hours=5) 
                    
                    consolidado.append({
                        'Fecha': fecha_local.strftime("%d %b | %H:%M"),
                        'Local': p['homeTeam']['name'],
                        'Visitante': p['awayTeam']['name'],
                        'L %': round(prob_l, 1),
                        'V %': round(100 - prob_l, 1),
                        'Favorito': p['homeTeam']['name'] if prob_l > 50 else p['awayTeam']['name'],
                        'Goles': total
                    })
        except: st.error("Límite de API alcanzado. Espera un poco.")
        
        status.update(label="✅ Scanner Finalizado", state="complete", expanded=False)

    if consolidado:
        df = pd.DataFrame(consolidado)
        
        # --- PANEL DE CONTROL ---
        idx_dorada = (df['L %'] - 50).abs().idxmax()
        st.markdown(f'<h3><span class="emoji">⭐</span>Picks de Élite: {seleccion}</h3>', unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            best = df.loc[idx_dorada]
            st.metric("🏆 APUESTA DORADA", best['Favorito'], f"{max(best['L %'], best['V %'])}% Prob.")
            st.info(f"📍 {best['Local']} vs {best['Visitante']} \n\n ⏰ {best['Fecha']}")
        
        with c2:
            heavy = df.loc[df['Goles'].idxmax()]
            st.metric("💀 APUESTA NEGRA", "Alta Prob. Goles", f"+{round(heavy['Goles'],1)}")
            st.info(f"📍 {heavy['Local']} vs {heavy['Visitante']} \n\n ⏰ {heavy['Fecha']}")

        # --- TABLA DE DATOS ---
        st.markdown('<h3><span class="emoji">📅</span>Calendario Completo</h3>', unsafe_allow_html=True)
        
        df_show = df[['Fecha', 'Local', 'Visitante', 'L %', 'V %', 'Favorito']]
        # Estilizamos los nombres para que se vean más fuertes
        st.dataframe(df_show, use_container_width=True, hide_index=True)
        
        st.caption("🚨 Datos basados en inteligencia estadística y rendimiento reciente.")

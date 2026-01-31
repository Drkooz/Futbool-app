import streamlit as st
import requests
import pandas as pd
import time
import random
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN VISUAL MAESTRA
st.set_page_config(page_title="Elite Predictor Pro", page_icon="⚽", layout="wide")

# CSS REFORZADO PARA ALTO CONTRASTE
st.markdown("""
    <style>
    /* Fondo General */
    .stApp {
        background-color: #000000;
        background-image: linear-gradient(rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.8)), 
        url("https://images.unsplash.com/photo-1508098682722-e99c43a406b2?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80");
        background-size: cover;
    }

    /* CONTENEDOR PRINCIPAL CON FONDO SÓLIDO */
    .block-container {
        background: rgba(20, 20, 20, 0.95) !important;
        border: 4px solid #39FF14 !important;
        border-radius: 20px;
        padding: 30px !important;
        box-shadow: 0 0 40px rgba(57, 255, 20, 0.4);
    }

    /* TEXTO CON MÁXIMO BRILLO */
    h1, h2, h3, h4, p, span, li {
        color: #FFFFFF !important;
        font-weight: 800 !important;
        text-shadow: 2px 2px 4px #000000 !important;
    }

    /* SELECTOR DE LIGA - FONDO CLARO PARA PC */
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border: 2px solid #39FF14 !important;
    }
    
    div[data-baseweb="select"] span, div[role="listbox"] span {
        color: #000000 !important;
        font-weight: bold !important;
    }

    /* TARJETAS DE MÉTRICAS CON FONDO MÁS CLARO */
    div[data-testid="stMetric"] {
        background: #1a1a1a !important;
        border: 2px solid #39FF14 !important;
        border-radius: 15px;
        padding: 20px !important;
    }

    /* VALORES DE LAS MÉTRICAS */
    div[data-testid="stMetricValue"] {
        color: #39FF14 !important;
        font-size: 32px !important;
    }

    /* BOTÓN ANALIZAR */
    .stButton>button {
        background: #39FF14 !important;
        color: #000000 !important;
        font-size: 20px !important;
        font-weight: bold !important;
        border-radius: 50px !important;
        height: 3em !important;
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Ligas con nombres en mayúsculas para mejor lectura
LIGAS_DICT = {
    "EUROPA - CHAMPIONS LEAGUE": 2001,
    "INGLATERRA - PREMIER LEAGUE": 2021,
    "ESPAÑA - LA LIGA": 2014,
    "ITALIA - SERIE A": 2019,
    "ALEMANIA - BUNDESLIGA": 2002,
    "FRANCIA - LIGUE 1": 2015
}

st.markdown('<h1>⚽ ELITE FOOTBALL SCANNER</h1>', unsafe_allow_html=True)
st.markdown('<p style="color: #39FF14 !important;">PROFESSIONAL DATA ANALYSIS</p>', unsafe_allow_html=True)

# Selector
seleccion = st.selectbox("📍 ELIGE TU LIGA ABAJO:", list(LIGAS_DICT.keys()))
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

if st.button(f'🏟️ ANALIZAR {seleccion}'):
    hoy = datetime.now()
    consolidado = []
    
    with st.status("🚀 PROCESANDO DATOS...", expanded=True) as status:
        try:
            url = f"https://api.football-data.org/v4/competitions/{liga_id}/matches"
            params = {'dateFrom': hoy.date(), 'dateTo': (hoy + timedelta(days=5)).date()}
            data = requests.get(url, headers=HEADERS, params=params).json()
            partidos = data.get('matches', [])
            
            if not partidos:
                st.warning("SIN PARTIDOS PRÓXIMOS.")
            else:
                for p in partidos[:4]:
                    st.write(f"✔ Analizando: {p['homeTeam']['name']}")
                    of_l, df_l = obtener_fuerza(p['homeTeam']['id'])
                    of_v, df_v = obtener_fuerza(p['awayTeam']['id'])
                    
                    p_l = ((of_l + df_v) / 2) * 1.15
                    p_v = ((of_v + df_l) / 2) * 0.85
                    total = p_l + p_v
                    prob_l = (p_l / total) * 100 if total > 0 else 50
                    
                    fecha_dt = datetime.strptime(p['utcDate'], "%Y-%m-%dT%H:%M:%SZ")
                    fecha_local = fecha_dt - timedelta(hours=5) 
                    
                    consolidado.append({
                        'FECHA': fecha_local.strftime("%d %b | %H:%M"),
                        'LOCAL': p['homeTeam']['name'],
                        'VISITA': p['awayTeam']['name'],
                        'L %': round(prob_l, 1),
                        'V %': round(100 - prob_l, 1),
                        'FAVORITO': p['homeTeam']['name'] if prob_l > 50 else p['awayTeam']['name'],
                        'GOLES': total
                    })
        except: st.error("LÍMITE DE API. ESPERA 1 MINUTO.")
        status.update(label="✅ ANÁLISIS LISTO", state="complete", expanded=False)

    if consolidado:
        df = pd.DataFrame(consolidado)
        idx_dorada = (df['L %'] - 50).abs().idxmax()
        
        st.markdown('## 🏆 SELECCIONES VIP')
        c1, c2 = st.columns(2)
        
        with c1:
            best = df.iloc[idx_dorada]
            st.metric("🏆 APUESTA DORADA", best['FAVORITO'], f"{max(best['L %'], best['V %'])}% PROB.")
            st.markdown(f"**PARTIDO:** {best['LOCAL']} vs {best['VISITA']}")
            st.markdown(f"**HORA:** {best['FECHA']}")
        
        with c2:
            heavy = df.loc[df['GOLES'].idxmax()]
            st.metric("💀 APUESTA NEGRA", f"{round(heavy['GOLES'],1)} GOLES", "OVER 2.5")
            st.markdown(f"**PARTIDO:** {heavy['LOCAL']} vs {heavy['VISITA']}")
            st.markdown(f"**HORA:** {heavy['FECHA']}")

        st.markdown('## 📊 CALENDARIO COMPLETO')
        # Tabla con fondo contrastado
        st.dataframe(df[['FECHA', 'LOCAL', 'VISITA', 'L %', 'V %', 'FAVORITO']], use_container_width=True, hide_index=True)

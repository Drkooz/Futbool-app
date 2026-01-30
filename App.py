import streamlit as st
import requests
import pandas as pd
import time
import random
from datetime import date, timedelta

# 1. CONFIGURACIÓN VISUAL Y CARGA DE ESTILOS
st.set_page_config(page_title="Elite Predictor", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    [data-testid="stMetricValue"] { font-size: 28px !important; color: #00ffcc !important; }
    .stButton>button { border-radius: 12px; background-color: #1a73e8; color: white; height: 3.8em; font-weight: bold; border: none; }
    .stButton>button:hover { background-color: #1557b0; border: none; }
    .stSelectbox label { color: #00ffcc !important; font-size: 20px; font-weight: bold; }
    .card { background-color: #1e2130; padding: 15px; border-radius: 10px; border-left: 5px solid #00ffcc; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ Elite Football Scanner")
st.write("Análisis estadístico profesional para tus apuestas.")

# --- DICCIONARIO DE LIGAS ---
LIGAS_DICT = {
    "🇪🇺 Champions League": 2001,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": 2021,
    "🇪🇸 La Liga": 2014,
    "🇮🇹 Serie A": 2019,
    "🇩🇪 Bundesliga": 2002,
    "🇫🇷 Ligue 1": 2015
}

seleccion = st.selectbox("🎯 Selecciona la liga para hoy:", list(LIGAS_DICT.keys()))
liga_id = LIGAS_DICT[seleccion]

API_KEY = "9ac6384534674eb593649352a93a2afc"
HEADERS = { 'X-Auth-Token': API_KEY }

MENSAJES_ESPERA = [
    "⚽ Analizando los últimos goles...", "🖥️ Revisando el VAR estadístico...", 
    "🏃 Calentando motores...", "🏟️ Abriendo las puertas del estadio...",
    "📋 Estudiando alineaciones...", "⏳ Calculando probabilidades..."
]

def obtener_fuerza(id_equipo):
    url = f"https://api.football-data.org/v4/teams/{id_equipo}/matches?status=FINISHED"
    try:
        time.sleep(11) # Respeto a la API (Máximo 10 req/min)
        res = requests.get(url, headers=HEADERS).json()
        p = res.get('matches', [])[-5:]
        if not p: return 1.0, 1.0
        g_m = sum(m['score']['fullTime']['home'] if m['homeTeam']['id'] == id_equipo else m['score']['fullTime']['away'] for m in p)
        g_r = sum(m['score']['fullTime']['away'] if m['homeTeam']['id'] == id_equipo else m['score']['fullTime']['home'] for m in p)
        return g_m/len(p), g_r/len(p)
    except: return 1.0, 1.0

if st.button(f'🚀 INICIAR ESCANEO DE {seleccion.upper()}'):
    hoy = date.today()
    consolidado = []
    
    with st.status(f"🔍 Analizando {seleccion}...", expanded=True) as status:
        try:
            url = f"https://api.football-data.org/v4/competitions/{liga_id}/matches"
            # Buscamos partidos para los próximos 4 días
            params = {'dateFrom': hoy, 'dateTo': hoy + timedelta(days=4)}
            data = requests.get(url, headers=HEADERS, params=params).json()
            partidos = data.get('matches', [])
            
            if not partidos:
                st.warning(f"No hay partidos programados pronto para {seleccion}.")
            else:
                # Procesamos los primeros 4 partidos para optimizar tiempo
                for p in partidos[:4]:
                    st.toast(random.choice(MENSAJES_ESPERA)) # Mensaje flotante de carga
                    l_nom, v_nom = p['homeTeam']['name'], p['awayTeam']['name']
                    of_l, df_l = obtener_fuerza(p['homeTeam']['id'])
                    of_v, df_v = obtener_fuerza(p['awayTeam']['id'])
                    
                    p_l = ((of_l + df_v) / 2) * 1.15
                    p_v = ((of_v + df_l) / 2) * 0.85
                    total_goles = p_l + p_v
                    prob_l = (p_l / total_goles) * 100 if total_goles > 0 else 50
                    prob_v = (p_v / total_goles) * 100 if total_goles > 0 else 50
                    
                    consolidado.append({
                        'Local': l_nom,
                        'Visitante': v_nom,
                        'L %': round(prob_l, 1),
                        'V %': round(prob_v, 1),
                        'Goles': round(total_goles, 2),
                        'Favorito': l_nom if prob_l > prob_v else v_nom
                    })
        except Exception as e:
            st.error("La API está saturada. Espera 1 minuto y vuelve a intentar.")
        
        status.update(label="✅ ¡Análisis Completo!", state="complete", expanded=False)

    if consolidado:
        df = pd.DataFrame(consolidado)
        
        # --- IDENTIFICACIÓN DE PICKS (Sin errores de índice) ---
        idx_dorada = (df['L %'] - df['V %']).abs().idxmax()
        idx_negra = df['Goles'].idxmax()
        
        st.subheader(f"🌟 Destacados de {seleccion}")
        col1, col2 = st.columns(2)
        
        with col1:
            best = df.loc[idx_dorada]
            st.metric("🏆 APUESTA DORADA", best['Favorito'], f"{max(best['L %'], best['V %'])}%")
            st.caption(f"Partido: {best['Local']} vs {best['Visitante']}")

        with col2:
            heavy = df.loc[idx_negra]
            st.metric("💀 APUESTA NEGRA", f"+{int(heavy['Goles'])} Goles", "Lluvia de Goles")
            st.caption(f"Partido: {heavy['Local']} vs {heavy['Visitante']}")

        st.divider()
        st.subheader("📋 Todas las Probabilidades")
        
        # Formato de tabla limpia para móvil
        df_view = df[['Local', 'Visitante', 'L %', 'V %', 'Favorito']]
        # Transformamos a string con % para estética
        df_view['L %'] = df_view['L %'].map('{:.1f}%'.format)
        df_view['V %'] = df_view['V %'].map('{:.1f}%'.format)
        
        st.dataframe(df_view, use_container_width=True, hide_index=True)
    else:
        st.info("No se encontraron datos. Selecciona otra liga o intenta más tarde.")

import streamlit as st
import requests
import pandas as pd
import time
from datetime import date, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Predicciones Elite", page_icon="⚽", layout="centered")

# Estilo visual simple (CSS)
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ Elite Football Scanner")
st.write("Pulsa el botón para analizar las mejores ligas de los próximos 4 días.")

# --- TU MOTOR (Lógica Interna) ---
API_KEY = "9ac6384534674eb593649352a93a2afc"
HEADERS = { 'X-Auth-Token': API_KEY }
LIGAS = [2001, 2021, 2014, 2019, 2002, 2015]

def obtener_fuerza(id_equipo):
    url = f"https://api.football-data.org/v4/teams/{id_equipo}/matches?status=FINISHED"
    try:
        time.sleep(11) # Respeto a la API
        res = requests.get(url, headers=HEADERS).json()
        p = res.get('matches', [])[-5:]
        if not p: return 1.0, 1.0
        g_m = sum(m['score']['fullTime']['home'] if m['homeTeam']['id'] == id_equipo else m['score']['fullTime']['away'] for m in p)
        g_r = sum(m['score']['fullTime']['away'] if m['homeTeam']['id'] == id_equipo else m['score']['fullTime']['home'] for m in p)
        return g_m/len(p), g_r/len(p)
    except: return 1.0, 1.0

# --- INTERFAZ DE USUARIO ---
if st.button("🚀 GENERAR REPORTE DE HOY"):
    progreso = st.progress(0)
    status_text = st.empty()
    
    hoy = date.today()
    consolidado = []
    
    # Escaneo
    for idx, liga_id in enumerate(LIGAS):
        status_text.text(f"Escaneando Liga {liga_id}...")
        progreso.progress((idx + 1) / len(LIGAS))
        
        try:
            url = f"https://api.football-data.org/v4/competitions/{liga_id}/matches"
            params = {'dateFrom': hoy, 'dateTo': hoy + timedelta(days=4)}
            data = requests.get(url, headers=HEADERS, params=params).json()
            partidos = data.get('matches', [])[:2] # Limitamos a 2 por liga para rapidez web
            
            for p in partidos:
                l_nom, v_nom = p['homeTeam']['name'], p['awayTeam']['name']
                of_l, df_l = obtener_fuerza(p['homeTeam']['id'])
                of_v, df_v = obtener_fuerza(p['awayTeam']['id'])
                
                p_l = ((of_l + df_v) / 2) * 1.15
                p_v = ((of_v + df_l) / 2) * 0.85
                
                consolidado.append({
                    'Partido': f"{l_nom} vs {v_nom}",
                    'Prob. Local': round(p_l, 1),
                    'Prob. Visita': round(p_v, 1),
                    'Favorito': l_nom if p_l > p_v else v_nom
                })
        except: continue

    status_text.success("¡Análisis completado!")
    
    # CUADRO GRÁFICO FINAL
    if consolidado:
        df = pd.DataFrame(consolidado)
        
        # Mostramos una tabla estilizada
        st.subheader("📊 Resultados Sugeridos")
        
        # Aplicamos colores a la tabla
        def highlight_fav(s):
            return ['background-color: #d4edda' if s.name == 'Favorito' else '' for _ in s]

        st.table(df) 
        st.info("Nota: Los datos se basan en los últimos 5 partidos de cada equipo.")
    else:
        st.warning("No se encontraron partidos en las próximas horas.")

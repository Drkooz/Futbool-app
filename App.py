import streamlit as st
import requests
import pandas as pd
import time
import random
from datetime import date, timedelta

# 1. CONFIGURACIÓN VISUAL PRO
st.set_page_config(page_title="Elite Predictor", page_icon="⚽", layout="wide")

# CSS personalizado para que se vea bien en el móvil
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    div[data-testid="stMetricValue"] { font-size: 24px; color: #00ffcc; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #2e7d32; color: white; height: 3.5em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ Elite Football Scanner v3.0")
st.write("Analizando las ligas TOP del mundo en tiempo real.")

# --- DATOS DE CONEXIÓN ---
API_KEY = "9ac6384534674eb593649352a93a2afc"
HEADERS = { 'X-Auth-Token': API_KEY }
LIGAS = [2001, 2021, 2014, 2019, 2002, 2015]

# Mensajes divertidos para la espera
MENSAJES_ESPERA = [
    "⚽ Inflando los balones...",
    "🖥️ Consultando al VAR...",
    "🏃 Los jugadores están calentando...",
    "🏟️ Regando el césped de los estadios...",
    "📋 Analizando tácticas de los entrenadores...",
    "👟 Lustrando los botines de las estrellas...",
    "🐙 Consultando con el sucesor del pulpo Paul...",
    "⏳ Calculando probabilidades de último minuto..."
]

def obtener_fuerza(id_equipo):
    url = f"https://api.football-data.org/v4/teams/{id_equipo}/matches?status=FINISHED"
    try:
        time.sleep(11) # Respeto necesario a la API
        res = requests.get(url, headers=HEADERS).json()
        p = res.get('matches', [])[-5:]
        if not p: return 1.0, 1.0
        g_m = sum(m['score']['fullTime']['home'] if m['homeTeam']['id'] == id_equipo else m['score']['fullTime']['away'] for m in p)
        g_r = sum(m['score']['fullTime']['away'] if m['homeTeam']['id'] == id_equipo else m['score']['fullTime']['home'] for m in p)
        return g_m/len(p), g_r/len(p)
    except: return 1.0, 1.0

# --- BOTÓN PRINCIPAL ---
if st.button('🚀 ESCANEAR JORNADA'):
    hoy = date.today()
    consolidado = []
    
    # Contenedor de mensajes de carga
    with st.status("🔍 Iniciando escaneo profundo...", expanded=True) as status:
        for liga_id in LIGAS:
            # Cambiamos el mensaje para que se sienta natural
            msg = random.choice(MENSAJES_ESPERA)
            st.write(msg)
            
            try:
                url = f"https://api.football-data.org/v4/competitions/{liga_id}/matches"
                params = {'dateFrom': hoy, 'dateTo': hoy + timedelta(days=4)}
                data = requests.get(url, headers=HEADERS, params=params).json()
                
                for p in data.get('matches', [])[:2]: # 2 partidos por liga para no tardar una eternidad
                    l_nom, v_nom = p['homeTeam']['name'], p['awayTeam']['name']
                    of_l, df_l = obtener_fuerza(p['homeTeam']['id'])
                    of_v, df_v = obtener_fuerza(p['awayTeam']['id'])
                    
                    p_l = ((of_l + df_v) / 2) * 1.15
                    p_v = ((of_v + df_l) / 2) * 0.85
                    total = p_l + p_v
                    prob_l = (p_l / total) * 100 if total > 0 else 50
                    prob_v = (p_v / total) * 100 if total > 0 else 50
                    
                    consolidado.append({
                        'Liga': data['competition']['name'],
                        'Local': l_nom,
                        'Visitante': v_nom,
                        'L %': round(prob_l, 1),
                        'V %': round(prob_v, 1),
                        'Goles': total,
                        'Favorito': l_nom if prob_l > prob_v else v_nom,
                        'Pick': 'Normal'
                    })
            except: continue
        
        status.update(label="✅ ¡Análisis completado!", state="complete", expanded=False)

    if consolidado:
        df = pd.DataFrame(consolidado)
        
        # ASIGNACIÓN DE PICKS ESPECIALES
        diffs = (df['L %'] - df['V %']).abs()
        df.loc[diffs.idxmax(), 'Pick'] = '🏆 DORADA'
        df.loc[df['Goles'].idxmax(), 'Pick'] = '💀 NEGRA'
        
        id_caballo = diffs.idxmin()
        if df.loc[id_caballo, 'Pick'] == 'Normal':
            df.loc[id_caballo, 'Pick'] = '🐎 CABALLO'

        # --- SECCIÓN DE TARJETAS (IDEAL PARA MÓVIL) ---
        st.subheader("🌟 Selecciones del Día")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            pick_d = df[df['Pick'] == '🏆 DORADA'].iloc[0]
            st.metric("🏆 APUESTA DORADA", pick_d['Favorito'], f"{pick_d['L %']}% vs {pick_d['V %']}%")
            st.caption(f"{pick_d['Local']} vs {pick_d['Visitante']}")

        with c2:
            pick_n = df[df['Pick'] == '💀 NEGRA'].iloc[0]
            st.metric("💀 APUESTA NEGRA", "Lluvia de Goles", f"+{round(pick_n['Goles'],1)} goles")
            st.caption(f"{pick_n['Local']} vs {pick_n['Visitante']}")

        with c3:
            pick_c = df[df['Pick'] == '🐎 CABALLO'].iloc[0]
            st.metric("🐎 CABALLO NEGRO", "Empate/Cerrado", "Riesgo Alto")
            st.caption(f"{pick_c['Local']} vs {pick_c['Visitante']}")

        # --- TABLA DETALLADA ---
        st.divider()
        st.subheader("📋 Calendario de Análisis")
        
        # Estética de tabla
        df_display = df[['Local', 'Visitante', 'L %', 'V %', 'Favorito', 'Liga']]
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        st.info("💡 Consejo: Abre esta app 1 hora antes de los partidos para datos más frescos.")
    else:
        st.warning("No se encontraron partidos próximos. Intenta mañana.")

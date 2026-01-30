import streamlit as st
import requests
import pandas as pd
import time
from datetime import date, timedelta

# Configuración visual Pro
st.set_page_config(page_title="Elite Predictor", page_icon="⚽", layout="wide")
st.title("⚽ Elite Football Scanner v2.0")

API_KEY = "9ac6384534674eb593649352a93a2afc"
HEADERS = { 'X-Auth-Token': API_KEY }
LIGAS = [2001, 2021, 2014, 2019, 2002, 2015]

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

if st.button('🚀 GENERAR PREDICCIONES Y PICKS'):
    hoy = date.today()
    consolidado = []
    bar = st.progress(0)
    
    for i, liga_id in enumerate(LIGAS):
        bar.progress((i + 1) / len(LIGAS))
        try:
            url = f"https://api.football-data.org/v4/competitions/{liga_id}/matches"
            params = {'dateFrom': hoy, 'dateTo': hoy + timedelta(days=4)}
            data = requests.get(url, headers=HEADERS, params=params).json()
            for p in data.get('matches', [])[:3]:
                l_id, l_nom = p['homeTeam']['id'], p['homeTeam']['name']
                v_id, v_nom = p['awayTeam']['id'], p['awayTeam']['name']
                of_l, df_l = obtener_fuerza(l_id)
                of_v, df_v = obtener_fuerza(v_id)
                
                # Predicción de goles
                p_l = ((of_l + df_v) / 2) * 1.15
                p_v = ((of_v + df_l) / 2) * 0.85
                
                # Cálculo de Porcentajes
                total = p_l + p_v
                prob_l = (p_l / total) * 100 if total > 0 else 50
                prob_v = (p_v / total) * 100 if total > 0 else 50
                
                consolidado.append({
                    'Liga': data['competition']['name'],
                    'Local': l_nom,
                    'Visitante': v_nom,
                    'Prob. Local %': round(prob_l, 1),
                    'Prob. Visita %': round(prob_v, 1),
                    'Goles Est.': round(total, 2),
                    'Favorito': l_nom if prob_l > prob_v else v_nom,
                    'Recomendación': 'Normal'
                })
        except: continue
    
    if consolidado:
        df = pd.DataFrame(consolidado)
        
        # LÓGICA DE MEDALLAS DINÁMICAS
        # 1. Dorada: Mayor diferencia entre local y visita
        diffs = (df['Prob. Local %'] - df['Prob. Visita %']).abs()
        df.loc[diffs.idxmax(), 'Recomendación'] = '🏆 DORADA'
        
        # 2. Negra: Mayor cantidad de goles totales (Espectáculo)
        df.loc[df['Goles Est.'].idxmax(), 'Recomendación'] = '💀 NEGRA'
        
        # 3. Caballo Negro: El partido más parejo (Diferencia mínima)
        id_caballo = diffs.idxmin()
        if df.loc[id_caballo, 'Recomendación'] == 'Normal':
            df.loc[id_caballo, 'Recomendación'] = '🐎 CABALLO NEGRO'

        # Mostrar tabla estilizada
        st.subheader("📊 Análisis de Probabilidades")
        
        # Formatear porcentajes para que luzcan como texto con %
        df_display = df.copy()
        df_display['Prob. Local %'] = df_display['Prob. Local %'].astype(str) + '%'
        df_display['Prob. Visita %'] = df_display['Prob. Visita %'].astype(str) + '%'
        
        st.dataframe(df_display[['Recomendación', 'Local', 'Visitante', 'Prob. Local %', 'Prob. Visita %', 'Favorito', 'Liga']], use_container_width=True)
        
        st.success("✨ Picks generados con éxito. ¡Mucha suerte!")
    else:
        st.write("No hay partidos próximos.")

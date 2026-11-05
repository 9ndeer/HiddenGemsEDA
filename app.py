import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os
import unicodedata
import re
import gdown

st.set_page_config(page_title="Scouting Hidden Gems Pro", layout="wide")
st.title("Hidden Gems: Scouting Interactivo y Análisis de Mercado")

# ==============================================================================
# DESCARGA AUTOMÁTICA DESDE GOOGLE DRIVE (Para Streamlit Cloud)
# ==============================================================================
@st.cache_resource
def descargar_datos_desde_drive():
    data_dir = "dataset_transfermarkt"
    os.makedirs(data_dir, exist_ok=True)
    
    # Enlaces de descarga configurados para tus archivos de Drive
    archivos = {
        "players_data-2025_2026.csv": "https://drive.google.com/file/d/1q70oG64yPL4Fo2vYs1MJv_-SeOjOzARj/view?usp=drive_link",
        "players.csv": "https://drive.google.com/file/d/1zjx4UmrXTTcpwS6lgE44YndMKvQK4ILx/view?usp=drive_link",
        "player_valuations.csv": "https://drive.google.com/file/d/1c0cEnNvtM9Ysnj6td3xKUxlgAf5yxzwQ/view?usp=drive_link"
    }
    
    for nombre_archivo, url_drive in archivos.items():
        ruta_local = os.path.join(data_dir, nombre_archivo)
        if not os.path.exists(ruta_local) and "1zjx4UmrXTTcpwS6lgE44YndMKvQK4ILx" not in url_drive:
            try:
                gdown.download(url_drive, ruta_local, fuzzy=True, quiet=True)
            except Exception as e:
                st.warning(f"No se pudo descargar automáticamente {nombre_archivo}: {e}")

# Ejecutar descarga al iniciar
descargar_datos_desde_drive()

# Usamos un selector en la barra lateral para cambiar de hipótesis/pestaña dinámicamente
st.sidebar.header("Navegación e Hipótesis")
seccion_activa = st.sidebar.radio(
    "Selecciona el Apartado:",
    [
        "Coeficiente de Eficiencia y Penalización", 
        "Análisis de Sobreprecio",
        "Scouting y Producción Ofensiva"
    ]
)

st.sidebar.markdown("---")
st.sidebar.header("Filtros Dinámicos")

# Mapa global de colores unificado para el Apartado 1
mapa_colores_cuartil = {
    '4 (Zona Alta)': '#27ae60',   # Verde (Élite/Alta)
    '3 (Media-Alta)': '#2980b9',  # Azul 
    '2 (Media-Baja)': '#f39c12',  # Naranja
    '1 (Zona Baja)': '#c0392b'    # Rojo (Baja)
}

# ==============================================================================
# SECCIÓN 1: COEFICIENTE DE EFICIENCIA PONDERADA Y PENALIZACIÓN
# ==============================================================================
if seccion_activa == "Coeficiente de Eficiencia y Penalización":
    st.subheader("Análisis Defensivo, de Eficiencia y Disciplinario de Mediocentros y Defensas")
    st.markdown("""
    Este apartado evalúa el rendimiento defensivo, la disciplina, el riesgo de amonestaciones y la distribución de balón 
    mediante enfoques cruzados e independientes. Se exige un mínimo de 1000 minutos jugados y permite filtrar por edad y valor de mercado. 
    """)

    ligas_fbref = {
        'Inglaterra (Premier League)': 'eng Premier League',
        'España (La Liga)': 'es La Liga', 
        'Italia (Serie A)': 'it Serie A', 
        'Alemania (Bundesliga)': 'de Bundesliga', 
        'Francia (Ligue 1)': 'fr Ligue 1'
    }
    
    liga_fbref_nombre = st.sidebar.selectbox("Selecciona la Liga para el Análisis:", list(ligas_fbref.keys()), key="liga_fbref_select")
    liga_fbref_id = ligas_fbref[liga_fbref_nombre]

    edad_maxima_def = st.sidebar.slider(
        "Filtrar por Edad Máxima:", 
        min_value=16, max_value=40, value=35, step=1,
        key="slider_edad_def_mf",
        help="Ajusta la edad máxima para el análisis."
    )

    valor_mercado_max = st.sidebar.slider(
        "Valor de Mercado Máximo (Millones €):",
        min_value=1.0, max_value=200.0, value=200.0, step=5.0,
        key="slider_valor_mercado_max",
        help="Filtra jugadores cuyo valor de mercado no supere esta cifra."
    )

    def clean_name(name):
        if pd.isna(name): return ""
        name_str = str(name).strip().lower()
        name_str = ''.join(c for c in unicodedata.normalize('NFD', name_str) if unicodedata.category(c) != 'Mn')
        name_str = re.sub(r'[^\w\s]', ' ', name_str)
        return re.sub(r'\s+', ' ', name_str).strip()

    # DICCIONARIO DE ALIAS EXACTOS
    alias_map = {
        'gabriel magalhaes': 'gabriel',
        'max kilman': 'maximilian kilman',
        'hwang hee chan': 'hee chan hwang',
        'toti gomes': 'toti',
        'idrissa gana gueye': 'idrissa gueye',
        'nicolas gonzalez': 'nico gonzalez',
        'emi buendia': 'emiliano buendia',
        'hannibal mejbri': 'hannibal',
        'yeremi pino': 'yeremy pino',
        'valentino livramento': 'tino livramento',
        'nico o reilly': 'nico o reilly',
        'eli junior kroupi': 'junior kroupi',
        'yehor yarmoliuk': 'yegor yarmolyuk',
        'daniel ballard': 'dan ballard',
        'florentino luis': 'florentino',
        'ferdi kadioglu': 'ferdi kadioglu',
        'lucas': 'lucas',
        'adam smith': 'adam smith',
        'castrin': 'castrin',
        'roberto navarro': 'robert navarro',
        'domingos andre ribeiro almeida': 'andre almeida',
        'joaquin martinez gauna': 'quique salas',
        'djene': 'dakonam djene',
        'iglesias': 'juan iglesias',
        'olasagasti': 'jon ander olasagasti',
        'francisco perez': 'fran perez',
        'catena': 'alejandro catena',
        'isaac palazon camacho': 'isi palazon',
        'jose luis garcia vaya': 'pepelu',
        'urko gonzalez': 'urko gonzalez de zarate',
        'brugui': 'roger brugue',
        'copete': 'jose copete',
        'rahim bonkano': 'abdel rahim alhassane',
        'lucas ahijado': 'lucas ahijado',
        'andre frank zambo anguissa': 'frank anguissa',
        'oliver nielsen': 'oliver nielsen',
        'albert gudmundsson': 'albert gudmundsson',
        'rafel obrador': 'rafa obrador',
        'leo skiri ostigard': 'leo ostigard',
        'ze pedro figueiredo': 'ze pedro',
        'michel ndary adopo': 'michel adopo',
        'kialonda': 'kialonda gaspar',
        'oliver jensen': 'oliver jensen',
        'romano floriani': 'romano floriani mussolini',
        'castrop jens': 'jens castrop',
        'ifechukwu ogbus': 'ifechukwu ogbus',
        'caio henrique oliveira silva': 'caio henrique',
        'igor carioca': 'igor silva',
        'dehmaime assoumani': 'dehmaine assoumani',
        'abdulai juma bah': 'abdulai juma bah'
    }

    @st.cache_data
    def cargar_datos_completos():
        df_full = pd.DataFrame()
        df_val = pd.DataFrame()
        df_players_map = pd.DataFrame()
        
        for path_prefix in ['.', 'dataset_transfermarkt']:
            f_full = os.path.join(path_prefix, 'players_data-2025_2026.csv')
            if os.path.exists(f_full) and df_full.empty:
                df_full = pd.read_csv(f_full)
                
            f_val = os.path.join(path_prefix, 'player_valuations.csv')
            if os.path.exists(f_val) and df_val.empty:
                df_val = pd.read_csv(f_val)
                
            f_map = os.path.join(path_prefix, 'players.csv')
            if os.path.exists(f_map) and df_players_map.empty:
                df_players_map = pd.read_csv(f_map)

        return df_full, df_val, df_players_map

    df_full_fbref, df_val, df_players_map = cargar_datos_completos()

    if not df_full_fbref.empty:
        df_liga_fbref = df_full_fbref[df_full_fbref['Comp'] == liga_fbref_id].copy()
        df_liga_fbref['Born_FB'] = pd.to_numeric(df_liga_fbref['Born'], errors='coerce')

        if not df_val.empty and not df_players_map.empty and 'market_value_in_eur' in df_val.columns:
            df_val['date'] = pd.to_datetime(df_val['date'], errors='coerce')
            df_val_latest = df_val.sort_values('date').groupby('player_id').tail(1).copy()
            df_val_latest['Market_Value_M'] = df_val_latest['market_value_in_eur'] / 1_000_000.0

            df_map_clean = df_players_map[['player_id', 'name', 'date_of_birth']].copy()
            df_map_clean['Player_clean_TM'] = df_map_clean['name'].apply(clean_name)
            df_map_clean['Born_TM'] = pd.to_datetime(df_map_clean['date_of_birth'], errors='coerce').dt.year
            
            df_val_merged = pd.merge(df_val_latest, df_map_clean, on='player_id', how='inner')

            df_liga_fbref['Player_clean_FB'] = df_liga_fbref['Player'].apply(clean_name)
            df_liga_fbref['Player_clean_FB'] = df_liga_fbref['Player_clean_FB'].replace(alias_map)

            def find_market_value(row):
                name_fb = row['Player_clean_FB']
                born_fb = row['Born_FB']
                matches = df_val_merged[df_val_merged['Player_clean_TM'] == name_fb]
                
                if matches.empty: return -1.0
                elif len(matches) == 1: return matches.iloc[0]['Market_Value_M']
                else:
                    if pd.notna(born_fb):
                        for _, match in matches.iterrows():
                            if pd.notna(match['Born_TM']) and abs(match['Born_TM'] - born_fb) <= 1:
                                return match['Market_Value_M']
                    return matches['Market_Value_M'].max()

            df_liga_fbref['Market_Value_M'] = df_liga_fbref.apply(find_market_value, axis=1)
        else:
            df_liga_fbref['Market_Value_M'] = -1.0

        if not df_liga_fbref.empty and {'W', 'D', 'L'}.issubset(df_liga_fbref.columns):
            team_stats = df_liga_fbref.groupby('Squad').agg({'W': 'max', 'D': 'max', 'L': 'max'}).reset_index()
            team_stats['Points'] = team_stats['W'] * 3 + team_stats['D']
            team_stats['Position'] = team_stats['Points'].rank(ascending=False, method='min')

            df_liga_pos = pd.merge(df_liga_fbref, team_stats[['Squad', 'Position']], on='Squad', how='left')
            df_def_mf = df_liga_pos[~df_liga_pos['Pos'].str.contains('GK', na=False) & (df_liga_pos['Pos'].str.contains('MF|DF', na=False))].copy()
            
            def clasificar_jugador(pos):
                if 'DF' in pos and 'MF' not in pos: return 'Defensa Puro (DF)'
                elif 'DF' in pos and 'MF' in pos: return 'Mediocentro / Defensivo (MF,DF)'
                elif 'FW' in pos: return 'Mediocentro / Ofensivo (MF,FW)'
                else: return 'Mediocentro / Puro (MF)'
                    
            df_def_mf['Tipo_Demarcacion'] = df_def_mf['Pos'].apply(clasificar_jugador)

            filtro_opciones = st.sidebar.selectbox("Filtrar por Demarcación:", ['Todos', 'Línea Defensiva Solo (DF)', 'Mediocentros Solo (MF)'], key="filtro_demarcacion_def_mf")
            if filtro_opciones == 'Línea Defensiva Solo (DF)':
                df_def_mf = df_def_mf[df_def_mf['Pos'].str.contains('DF', na=False) & ~df_def_mf['Pos'].str.contains('MF', na=False)]
            elif filtro_opciones == 'Mediocentros Solo (MF)':
                df_def_mf = df_def_mf[df_def_mf['Pos'].str.contains('MF', na=False)]

            df_def_mf['edad_final'] = pd.to_numeric(df_def_mf['Age'], errors='coerce').fillna(25)
            df_def_mf['valor_mercado_num'] = df_def_mf['Market_Value_M'].fillna(-1.0) if 'Market_Value_M' in df_def_mf.columns else -1.0

            df_def_mf = df_def_mf[
                (df_def_mf['Min'] >= 1000) & 
                (df_def_mf['edad_final'] <= edad_maxima_def) & 
                ((df_def_mf['valor_mercado_num'] == -1.0) | (df_def_mf['valor_mercado_num'] <= valor_mercado_max))
            ].copy()

            if not df_def_mf.empty:
                df_def_mf['Tabla_Cuartil'] = pd.qcut(df_def_mf['Position'], 4, labels=['4 (Zona Alta)', '3 (Media-Alta)', '2 (Media-Baja)', '1 (Zona Baja)'])
                df_def_mf['90s'] = df_def_mf['90s'].replace(0, np.nan)
                df_def_mf['Fls'] = df_def_mf['Fls'].replace(0, 0.1) 
                
                df_def_mf['Entradas_p90'] = (df_def_mf['TklW'] / df_def_mf['90s']).round(2)
                df_def_mf['Intercepciones_p90'] = (df_def_mf['Int'] / df_def_mf['90s']).round(2)
                df_def_mf['Ratio_Limpieza'] = (df_def_mf['TklW'] / df_def_mf['Fls']).round(2)
                
                col_impacto = '+/-90' if '+/-90' in df_def_mf.columns else ([c for c in df_def_mf.columns if '90' in c and ('+/-' in c or 'plus' in c.lower())] + [None])[0]
                df_def_mf['Impacto_+/-90'] = df_def_mf[col_impacto] if col_impacto and col_impacto in df_def_mf.columns else 0.0
                
                df_def_mf['Centros_p90'] = (df_def_mf['Crs'] / df_def_mf['90s']).round(2) if 'Crs' in df_def_mf.columns else 0.0
                df_def_mf['Tarjetas_Totales'] = df_def_mf['CrdY'].fillna(0) + df_def_mf['CrdR'].fillna(0)
                df_def_mf = df_def_mf.dropna(subset=['Entradas_p90', 'Intercepciones_p90', 'Ratio_Limpieza', 'TklW', 'Int']).copy()

                def preparar_datos_metrica(df, col_metrica, col_orden):
                    df_ordenado = df.sort_values(by=['Tabla_Cuartil', col_orden], ascending=[False, False])
                    top3_nombres = df_ordenado.groupby(['Tabla_Cuartil'], observed=False)['Player'].apply(lambda x: '<br>'.join(x.head(3))).reset_index(name='Top3_Nombres')
                    media_cuartil = df.groupby(['Tabla_Cuartil'], observed=False).agg(Media_Valor=(col_metrica, 'mean')).reset_index()
                    df_final = pd.merge(media_cuartil, top3_nombres, on=['Tabla_Cuartil'])
                    df_final['Media_Valor'] = df_final['Media_Valor'].round(2)
                    df_final['Eje_X_Label'] = df_final['Tabla_Cuartil'].astype(str) + '<br><b>Top 3:</b><br>' + df_final['Top3_Nombres']
                    return df_final

                # ==============================================================
                # 1. GRÁFICAS DE INTERRELACIÓN EN UNA SOLA COLUMNA (VERTICAL)
                # ==============================================================
                st.markdown("---")
                st.subheader("Interrelación Gráfica Interactiva: Defensa, Disciplina y Distribución")
                st.markdown("Haz clic en cualquier punto (jugador) de los gráficos de dispersión para desplegar su ficha completa de rendimiento.")

                def mostrar_ficha_jugador_clic_ampliada(fig_scatter, df_source, key_grafico):
                    evento = st.plotly_chart(fig_scatter, use_container_width=True, on_select="rerun", key=key_grafico)
                    if evento and "selection" in evento and evento["selection"]["points"]:
                        punto = evento["selection"]["points"][0]
                        nombre_jugador = punto.get("hovertext")
                        if not nombre_jugador and "point_index" in punto:
                            idx = punto["point_index"]
                            if idx < len(df_source):
                                nombre_jugador = df_source.iloc[idx]['Player']

                        if nombre_jugador:
                            jugador_info = df_source[df_source['Player'] == nombre_jugador]
                            if not jugador_info.empty:
                                j = jugador_info.iloc[0]
                                p_mp = j.get('MP', 'N/D'); p_starts = j.get('Starts', 'N/D'); p_min = j.get('Min', 'N/D')
                                p_gls = j.get('Gls', 0); p_ast = j.get('Ast', 0); p_ga = j.get('G+A', 0)
                                p_crd_y = j.get('CrdY', 0); p_crd_r = j.get('CrdR', 0); p_fls = j.get('Fls', 0); p_fld = j.get('Fld', 0)
                                p_tkl = j.get('TklW', 0); p_int = j.get('Int', 0)
                                p_ong = j.get('onG', 'N/D'); p_onga = j.get('onGA', 'N/D'); p_net = j.get('+/-', 'N/D'); p_net90 = j.get('+/-90', 'N/D')
                                p_vm = j.get('valor_mercado_num', -1.0)
                                str_vm = f"{p_vm:.1f} M€" if p_vm != -1.0 else "No disponible"
                                
                                st.markdown("---")
                                st.info(f"""
                                **Ficha Ampliada del Jugador Seleccionado:**
                                - **Nombre y Nacionalidad:** {j['Player']} ({j.get('Nation', 'N/D')})
                                - **Equipo y Competición:** {j['Squad']} | {j.get('Comp', 'N/D')}
                                - **Demarcación y Perfil:** {j.get('Tipo_Demarcacion', j.get('Pos', 'N/D'))}
                                - **Edad / Valor de Mercado:** {j.get('edad_final', 'N/D')} años | **{str_vm}**
                                
                                **Participación y Regularidad:**
                                - **Partidos Jugados (Titularidades):** {p_mp} ({p_starts} titularidades)
                                - **Minutos Totales:** {p_min} min ({j.get('90s', 0)} partidos completos equivalentes)
                                
                                **Rendimiento Defensivo y Disciplina:**
                                - **Entradas Ganadas (TklW):** {p_tkl} ({j.get('Entradas_p90', 0)} p/90)
                                - **Intercepciones (Int):** {p_int} ({j.get('Intercepciones_p90', 0)} p/90)
                                - **Ratio de Limpieza (Entradas / Faltas):** {j.get('Ratio_Limpieza', 0)} (Faltas cometidas: {p_fls} | Recibidas: {p_fld})
                                - **Tarjetas:** {p_crd_y} Amarillas | {p_crd_r} Rojas (Total: {p_crd_y + p_crd_r})
                                
                                **Aportación Ofensiva y Distribución:**
                                - **Goles (Gls) + Asistencias (Ast):** {p_gls} Goles | {p_ast} Asistencias (Total G+A: {p_ga})
                                - **Centros (Crs):** {j.get('Crs', 0)} ({j.get('Centros_p90', 0)} p/90)
                                
                                **Impacto Colectivo (On-Off / +/-):**
                                - **Goles a favor / en contra del equipo con él en campo:** {p_ong} GF / {p_onga} GC
                                - **Impacto Neto (+/-):** {p_net} goles ({p_net90} por cada 90 minutos)
                                """)

                # Gráfico A
                st.markdown("### A. Entradas p/90 vs. Limpieza")
                fig_cruce1 = px.scatter(df_def_mf, x='Entradas_p90', y='Ratio_Limpieza', color='Tabla_Cuartil', color_discrete_map=mapa_colores_cuartil, hover_name='Player', hover_data=['Squad', 'Min'], labels={'Entradas_p90': 'Entradas (p/90)', 'Ratio_Limpieza': 'Ratio Limpieza', 'Tabla_Cuartil': 'Cuartil'})
                mostrar_ficha_jugador_clic_ampliada(fig_cruce1.update_layout(height=400), df_def_mf, "cruce_1")
                st.markdown("<p style='font-size:0.9em; color:gray'>ℹ️ <b>¿Qué compara y por qué?:</b> Cruza la cantidad de robos directos (Entradas) con la solvencia para hacerlo sin hacer falta (Limpieza). Destaca a los defensas proactivos pero limpios, penalizando a los que roban mucho a base de excesivas infracciones.</p>", unsafe_allow_html=True)

                # Gráfico B
                st.markdown("### B. Intercepciones p/90 vs. Entradas")
                fig_cruce2 = px.scatter(df_def_mf, x='Intercepciones_p90', y='Entradas_p90', color='Tabla_Cuartil', color_discrete_map=mapa_colores_cuartil, hover_name='Player', hover_data=['Squad', 'Min'], labels={'Intercepciones_p90': 'Intercepciones (p/90)', 'Entradas_p90': 'Entradas (p/90)', 'Tabla_Cuartil': 'Cuartil'})
                mostrar_ficha_jugador_clic_ampliada(fig_cruce2.update_layout(height=400), df_def_mf, "cruce_2")
                st.markdown("<p style='font-size:0.9em; color:gray'>ℹ️ <b>¿Qué compara y por qué?:</b> Enfrenta la anticipación táctica (Intercepciones) contra el duelo directo y físico (Entradas). Define el perfil del jugador: si prefiere leer el juego y cortar líneas de pase, o ir directamente al choque contra el rival.</p>", unsafe_allow_html=True)

                # Gráfico C
                st.markdown("### C. Impacto (+/- 90) vs. Volumen Defensivo")
                fig_cruce3 = px.scatter(df_def_mf, x='Entradas_p90', y='Impacto_+/-90', color='Tabla_Cuartil', color_discrete_map=mapa_colores_cuartil, hover_name='Player', hover_data=['Squad', 'Min'], labels={'Entradas_p90': 'Entradas (p/90)', 'Impacto_+/-90': 'Impacto (+/- 90)', 'Tabla_Cuartil': 'Cuartil'})
                mostrar_ficha_jugador_clic_ampliada(fig_cruce3.update_layout(height=400), df_def_mf, "cruce_3")
                st.markdown("<p style='font-size:0.9em; color:gray'>ℹ️ <b>¿Qué compara y por qué?:</b> Cruza el éxito colectivo del equipo con el jugador en campo (+/-) frente a su volumen de robos. Es vital para detectar 'Talentos Ocultos': defensores de equipos modestos o en la zona baja (rojos) que sostienen defensivamente a su plantilla aportando un impacto inusualmente positivo.</p>", unsafe_allow_html=True)

                # Gráfico D
                st.markdown("### D. Solidez (Int) vs. Centros")
                fig_cruce4 = px.scatter(df_def_mf, x='Intercepciones_p90', y='Centros_p90', color='Tabla_Cuartil', color_discrete_map=mapa_colores_cuartil, hover_name='Player', hover_data=['Squad', 'Min'], labels={'Intercepciones_p90': 'Intercepciones (p/90)', 'Centros_p90': 'Centros (p/90)', 'Tabla_Cuartil': 'Cuartil'})
                mostrar_ficha_jugador_clic_ampliada(fig_cruce4.update_layout(height=400), df_def_mf, "cruce_4")
                st.markdown("<p style='font-size:0.9em; color:gray'>ℹ️ <b>¿Qué compara y por qué?:</b> Evalúa la relación entre la solidez de corte (Intercepciones) y la capacidad ofensiva/distribución (Centros). Identifica perfiles muy completos (típicamente carrileros o pivotes creativos) que participan activamente en ambas áreas.</p>", unsafe_allow_html=True)

                # Gráfico E
                st.markdown("### E. Entradas vs. Tarjetas")
                fig_cruce5 = px.scatter(df_def_mf, x='Entradas_p90', y='Tarjetas_Totales', color='Tabla_Cuartil', color_discrete_map=mapa_colores_cuartil, hover_name='Player', hover_data=['Squad', 'Min', 'CrdY', 'CrdR'], labels={'Entradas_p90': 'Entradas (p/90)', 'Tarjetas_Totales': 'Total Tarjetas', 'Tabla_Cuartil': 'Cuartil'})
                mostrar_ficha_jugador_clic_ampliada(fig_cruce5.update_layout(height=400), df_def_mf, "cruce_5")
                st.markdown("<p style='font-size:0.9em; color:gray'>ℹ️ <b>¿Qué compara y por qué?:</b> Mide el factor de riesgo disciplinario. Expone a aquellos jugadores que, si bien ganan muchas entradas, cruzan constantemente la línea de la legalidad costándole amonestaciones recurrentes a su equipo.</p>", unsafe_allow_html=True)

                # ==============================================================
                # 2. MÉTRICAS INDIVIDUALES (TABLAS Y BARRAS A COLOR) ABAJO
                # ==============================================================
                
                # 1. Gráfica de Impacto (+/- 90)
                st.markdown("---")
                st.subheader(f"1. Tablas y Medias: Impacto (+/- 90) en **{liga_fbref_nombre}**")
                tabla_imp = df_def_mf[['Player', 'Squad', 'Tipo_Demarcacion', 'Tabla_Cuartil', 'Impacto_+/-90', 'valor_mercado_num', 'edad_final']].sort_values(by='Impacto_+/-90', ascending=False)
                tabla_imp['valor_mercado_num'] = tabla_imp['valor_mercado_num'].apply(lambda x: f"{x:.1f} M€" if x != -1.0 else "N/D")
                tabla_imp.columns = ['Nombre', 'Equipo', 'Demarcación', 'Cuartil', 'Impacto (+/- 90)', 'V. Mercado', 'Edad']
                st.dataframe(tabla_imp, use_container_width=True, hide_index=True)
                fig_imp = px.bar(preparar_datos_metrica(df_def_mf, 'Impacto_+/-90', 'Impacto_+/-90'), x='Eje_X_Label', y='Media_Valor', color='Tabla_Cuartil', color_discrete_map=mapa_colores_cuartil, text='Media_Valor', title="Media Global del Cuartil (Impacto)", labels={'Media_Valor': 'Media Impacto (+/- 90)', 'Eje_X_Label': 'Cuartil y Top 3', 'Tabla_Cuartil': 'Cuartil'})
                fig_imp.update_traces(texttemplate='%{text}', textposition='inside')
                fig_imp.update_layout(height=500, xaxis_tickangle=0, margin=dict(t=50, b=100))
                st.plotly_chart(fig_imp, use_container_width=True)

                # 2. Gráfica de Limpieza Defensiva
                st.markdown("---")
                st.subheader(f"2. Tablas y Medias: Limpieza Defensiva (Entradas/Faltas)")
                tabla_lim = df_def_mf[['Player', 'Squad', 'Tipo_Demarcacion', 'Tabla_Cuartil', 'Ratio_Limpieza', 'valor_mercado_num', 'edad_final']].sort_values(by='Ratio_Limpieza', ascending=False)
                tabla_lim['valor_mercado_num'] = tabla_lim['valor_mercado_num'].apply(lambda x: f"{x:.1f} M€" if x != -1.0 else "N/D")
                tabla_lim.columns = ['Nombre', 'Equipo', 'Demarcación', 'Cuartil', 'Limpieza (Entradas/Faltas)', 'V. Mercado', 'Edad']
                st.dataframe(tabla_lim, use_container_width=True, hide_index=True)
                fig_lim = px.bar(preparar_datos_metrica(df_def_mf, 'Ratio_Limpieza', 'Ratio_Limpieza'), x='Eje_X_Label', y='Media_Valor', color='Tabla_Cuartil', color_discrete_map=mapa_colores_cuartil, text='Media_Valor', title="Media Global del Cuartil (Limpieza Defensiva)", labels={'Media_Valor': 'Media Ratio Limpieza', 'Eje_X_Label': 'Cuartil y Top 3', 'Tabla_Cuartil': 'Cuartil'})
                fig_lim.update_traces(texttemplate='%{text}', textposition='inside')
                fig_lim.update_layout(height=500, xaxis_tickangle=0, margin=dict(t=50, b=100))
                st.plotly_chart(fig_lim, use_container_width=True)

                # 3. Gráfica de Entradas p/90
                st.markdown("---")
                st.subheader(f"3. Tablas y Medias: Volumen de Entradas (p/90)")
                tabla_tkl = df_def_mf[['Player', 'Squad', 'Tipo_Demarcacion', 'Tabla_Cuartil', 'Entradas_p90', 'TklW', 'valor_mercado_num', 'edad_final']].sort_values(by='Entradas_p90', ascending=False)
                tabla_tkl['valor_mercado_num'] = tabla_tkl['valor_mercado_num'].apply(lambda x: f"{x:.1f} M€" if x != -1.0 else "N/D")
                tabla_tkl.columns = ['Nombre', 'Equipo', 'Demarcación', 'Cuartil', 'Entradas (p/90)', 'Entradas Totales', 'V. Mercado', 'Edad']
                st.dataframe(tabla_tkl, use_container_width=True, hide_index=True)
                fig_tkl = px.bar(preparar_datos_metrica(df_def_mf, 'Entradas_p90', 'Entradas_p90'), x='Eje_X_Label', y='Media_Valor', color='Tabla_Cuartil', color_discrete_map=mapa_colores_cuartil, text='Media_Valor', title="Media Global del Cuartil (Entradas p/90)", labels={'Media_Valor': 'Media Entradas p/90', 'Eje_X_Label': 'Cuartil y Top 3', 'Tabla_Cuartil': 'Cuartil'})
                fig_tkl.update_traces(texttemplate='%{text}', textposition='inside')
                fig_tkl.update_layout(height=500, xaxis_tickangle=0, margin=dict(t=50, b=100))
                st.plotly_chart(fig_tkl, use_container_width=True)

                # 4. Gráfica de Intercepciones p/90
                st.markdown("---")
                st.subheader(f"4. Tablas y Medias: Volumen de Intercepciones (p/90)")
                tabla_int = df_def_mf[['Player', 'Squad', 'Tipo_Demarcacion', 'Tabla_Cuartil', 'Intercepciones_p90', 'Int', 'valor_mercado_num', 'edad_final']].sort_values(by='Intercepciones_p90', ascending=False)
                tabla_int['valor_mercado_num'] = tabla_int['valor_mercado_num'].apply(lambda x: f"{x:.1f} M€" if x != -1.0 else "N/D")
                tabla_int.columns = ['Nombre', 'Equipo', 'Demarcación', 'Cuartil', 'Intercepciones (p/90)', 'Intercep. Totales', 'V. Mercado', 'Edad']
                st.dataframe(tabla_int, use_container_width=True, hide_index=True)
                fig_int_bar = px.bar(preparar_datos_metrica(df_def_mf, 'Intercepciones_p90', 'Intercepciones_p90'), x='Eje_X_Label', y='Media_Valor', color='Tabla_Cuartil', color_discrete_map=mapa_colores_cuartil, text='Media_Valor', title="Media Global del Cuartil (Intercepciones p/90)", labels={'Media_Valor': 'Media Intercepciones p/90', 'Eje_X_Label': 'Cuartil y Top 3', 'Tabla_Cuartil': 'Cuartil'})
                fig_int_bar.update_traces(texttemplate='%{text}', textposition='inside')
                fig_int_bar.update_layout(height=500, xaxis_tickangle=0, margin=dict(t=50, b=100))
                st.plotly_chart(fig_int_bar, use_container_width=True)

                # 5. Gráfica de Centros / Distribución
                st.markdown("---")
                st.subheader(f"5. Tablas y Medias: Distribución y Centros (Crs p/90)")
                tabla_crs = df_def_mf[['Player', 'Squad', 'Tipo_Demarcacion', 'Tabla_Cuartil', 'Centros_p90', 'valor_mercado_num', 'edad_final']].sort_values(by='Centros_p90', ascending=False)
                tabla_crs['valor_mercado_num'] = tabla_crs['valor_mercado_num'].apply(lambda x: f"{x:.1f} M€" if x != -1.0 else "N/D")
                tabla_crs.columns = ['Nombre', 'Equipo', 'Demarcación', 'Cuartil', 'Centros (p/90)', 'V. Mercado', 'Edad']
                st.dataframe(tabla_crs, use_container_width=True, hide_index=True)
                fig_crs = px.bar(preparar_datos_metrica(df_def_mf, 'Centros_p90', 'Centros_p90'), x='Eje_X_Label', y='Media_Valor', color='Tabla_Cuartil', color_discrete_map=mapa_colores_cuartil, text='Media_Valor', title="Media Global del Cuartil (Centros p/90)", labels={'Media_Valor': 'Media Centros p/90', 'Eje_X_Label': 'Cuartil y Top 3', 'Tabla_Cuartil': 'Cuartil'})
                fig_crs.update_traces(texttemplate='%{text}', textposition='inside')
                fig_crs.update_layout(height=500, xaxis_tickangle=0, margin=dict(t=50, b=100))
                st.plotly_chart(fig_crs, use_container_width=True)

                # 6. Gráfica de Disciplina y Riesgo
                st.markdown("---")
                st.subheader(f"6. Tablas y Medias: Disciplina (Tarjetas Totales)")
                tabla_disc = df_def_mf[['Player', 'Squad', 'Tipo_Demarcacion', 'Tabla_Cuartil', 'Entradas_p90', 'CrdY', 'CrdR', 'Tarjetas_Totales', 'valor_mercado_num', 'edad_final']].sort_values(by='Tarjetas_Totales', ascending=False)
                tabla_disc['valor_mercado_num'] = tabla_disc['valor_mercado_num'].apply(lambda x: f"{x:.1f} M€" if x != -1.0 else "N/D")
                tabla_disc.columns = ['Nombre', 'Equipo', 'Demarcación', 'Cuartil', 'Entradas (p/90)', 'Amarillas', 'Rojas', 'Total Tarjetas', 'V. Mercado', 'Edad']
                st.dataframe(tabla_disc, use_container_width=True, hide_index=True)
                fig_disc_bar = px.bar(preparar_datos_metrica(df_def_mf, 'Tarjetas_Totales', 'Tarjetas_Totales'), x='Eje_X_Label', y='Media_Valor', color='Tabla_Cuartil', color_discrete_map=mapa_colores_cuartil, text='Media_Valor', title="Media Global del Cuartil (Tarjetas Totales)", labels={'Media_Valor': 'Media Tarjetas Totales', 'Eje_X_Label': 'Cuartil y Top 3', 'Tabla_Cuartil': 'Cuartil'})
                fig_disc_bar.update_traces(texttemplate='%{text}', textposition='inside')
                fig_disc_bar.update_layout(height=500, xaxis_tickangle=0, margin=dict(t=50, b=100))
                st.plotly_chart(fig_disc_bar, use_container_width=True)

            else:
                st.warning(f"No se encontraron jugadores con los filtros seleccionados (Min. 1000 min, máx. {edad_maxima_def} años y máx. {valor_mercado_max}M€). Prueba a ampliar el rango en la barra lateral.")
        else:
            st.warning("No se encontraron las columnas de clasificación (W, D, L) en los archivos CSV.")

# ==============================================================================
# SECCIÓN 2: ANÁLISIS DE SOBREPRECIO
# ==============================================================================
elif seccion_activa == "Análisis de Sobreprecio":
    st.subheader("Análisis de Sobreprecio: Demarcaciones por Liga, Cuartiles de Precio y Edad")
    st.markdown("""
    Esta pestaña analiza la Hipótesis 3 permitiendo seleccionar una liga específica, 
    evaluar los cuartiles de precio y filtrar de forma dinámica por edad máxima mediante la barra deslizadora.
    """)

    @st.cache_data
    def cargar_datos_sobreprecio_avanzado():
        df_fbref = pd.DataFrame()
        df_players = pd.DataFrame()
        
        f_full = 'players_data-2025_2026.csv'
        f_players_tm = os.path.join('dataset_transfermarkt', 'players.csv')
        
        if not os.path.exists(f_full):
            f_full = os.path.join('dataset_transfermarkt', 'players_data-2025_2026.csv')

        try:
            if os.path.exists(f_full):
                df_fbref = pd.read_csv(f_full)
            if os.path.exists(f_players_tm):
                df_players = pd.read_csv(f_players_tm)
        except Exception as e:
            st.error(f"Error cargando los archivos: {e}")
            
        return df_fbref, df_players

    df_fbref_val, df_players_val = cargar_datos_sobreprecio_avanzado()

    if not df_fbref_val.empty and not df_players_val.empty:
        col_precio_tm = 'market_value_in_eur' if 'market_value_in_eur' in df_players_val.columns else None
        col_edad_tm = 'age' if 'age' in df_players_val.columns else ('date_of_birth' if 'date_of_birth' in df_players_val.columns else None)
        
        cols_a_extraer = ['name']
        if col_precio_tm:
            cols_a_extraer.append(col_precio_tm)
        if col_edad_tm:
            cols_a_extraer.append(col_edad_tm)

        if col_precio_tm and 'name' in df_players_val.columns:
            df_players_sub = df_players_val[cols_a_extraer].drop_duplicates(subset=['name'])
            df_val_merged = pd.merge(df_fbref_val, df_players_sub, left_on='Player', right_on='name', how='inner')
        else:
            df_val_merged = df_fbref_val.copy()
            if col_precio_tm and col_precio_tm not in df_val_merged.columns:
                df_val_merged[col_precio_tm] = 0

        if not col_precio_tm or col_precio_tm not in df_val_merged.columns:
            col_precio_tm = 'market_value_in_eur'
            df_val_merged[col_precio_tm] = 5000000 

        if col_precio_tm in df_val_merged.columns:
            def categorizar_posicion(pos):
                if pd.isna(pos): return 'Otro'
                if 'FW' in pos: return 'Atacantes (FW)'
                elif 'MF' in pos: return 'Mediocentros (MF)'
                elif 'DF' in pos: return 'Defensas (DF)'
                else: return 'Porteros (GK)'

            df_val_merged['Demarcacion'] = df_val_merged['Pos'].apply(categorizar_posicion)
            
            if 'Age' in df_val_merged.columns:
                df_val_merged['edad_final'] = pd.to_numeric(df_val_merged['Age'], errors='coerce')
            elif col_edad_tm == 'age' and 'age' in df_val_merged.columns:
                df_val_merged['edad_final'] = pd.to_numeric(df_val_merged['age'], errors='coerce')
            elif col_edad_tm == 'date_of_birth' and 'date_of_birth' in df_val_merged.columns:
                df_val_merged['edad_final'] = 2026 - pd.to_datetime(df_val_merged['date_of_birth'], errors='coerce').dt.year
            else:
                df_val_merged['edad_final'] = 25

            df_val_merged['edad_final'] = df_val_merged['edad_final'].fillna(25)

            ligas_disponibles = sorted(df_val_merged['Comp'].dropna().unique().tolist())
            liga_seleccionada = st.sidebar.selectbox("Selecciona la Liga a Analizar:", ligas_disponibles, key="select_liga_p4")

            edad_maxima = st.sidebar.slider("Filtrar por Edad Máxima (Jóvenes Promesas / Sub-N):", min_value=16, max_value=40, value=23, step=1, key="slider_edad_p4")

            df_analisis = df_val_merged[
                (df_val_merged['Comp'] == liga_seleccionada) &
                (df_val_merged['Demarcacion'] != 'Porteros (GK)') & 
                (df_val_merged['Min'] >= 500) &
                (df_val_merged['edad_final'] <= edad_maxima)
            ].copy()
            
            df_analisis['Valor_Mundo_M'] = df_analisis[col_precio_tm] / 1e6

            if not df_analisis.empty:
                st.markdown("---")
                st.markdown(f"### Coste Medio por Demarcación en **{liga_seleccionada}** (Jugadores de hasta {edad_maxima} años)")

                resumen_dem = df_analisis.groupby('Demarcacion', observed=False).agg(
                    Jugadores=('Player', 'count'),
                    Valor_Medio_M=('Valor_Mundo_M', 'mean'),
                    G_A_p90=('G+A', lambda x: (x / df_analisis.loc[x.index, '90s']).mean() if '90s' in df_analisis.columns else 0)
                ).reset_index().round(2)

                resumen_dem.rename(columns={'Demarcacion': 'Demarcación', 'Jugadores': 'Nº Jugadores', 'Valor_Medio_M': 'Precio Medio (M€)', 'G_A_p90': 'Media G+A (p/90)'}, inplace=True)
                st.dataframe(resumen_dem, use_container_width=True, hide_index=True)

                st.markdown("---")
                st.markdown("### Cuartiles de Precio de Mercado por Demarcación")
                df_analisis['Cuartil_Precio'] = pd.qcut(df_analisis['Valor_Mundo_M'].fillna(0), 4, labels=['1 (Económico)', '2 (Medio-Bajo)', '3 (Medio-Alto)', '4 (Élite)'])

                resumen_cuartiles = df_analisis.groupby(['Demarcacion', 'Cuartil_Precio'], observed=False).agg(
                    Precio_Min=('Valor_Mundo_M', 'min'), Precio_Max=('Valor_Mundo_M', 'max'), Precio_Medio=('Valor_Mundo_M', 'mean'), Total_Jugadores=('Player', 'count')
                ).reset_index().round(2)

                resumen_cuartiles.rename(columns={'Demarcacion': 'Demarcación', 'Cuartil_Precio': 'Cuartil de Precio', 'Precio_Min': 'Precio Mínimo (M€)', 'Precio_Max': 'Precio Máximo (M€)', 'Precio_Medio': 'Precio Medio (M€)', 'Total_Jugadores': 'Nº Jugadores'}, inplace=True)
                st.dataframe(resumen_cuartiles, use_container_width=True, hide_index=True)

                fig_cuartiles = px.bar(resumen_cuartiles, x='Demarcación', y='Precio Medio (M€)', color='Cuartil de Precio', barmode='group', text='Precio Medio (M€)', title=f"Precio Medio por Cuartil en {liga_seleccionada} (Sub-{edad_maxima})")
                fig_cuartiles.update_traces(texttemplate='%{text} M€', textposition='outside')
                fig_cuartiles.update_layout(height=500, margin=dict(t=50))
                st.plotly_chart(fig_cuartiles, use_container_width=True)
            else:
                st.warning(f"No hay jugadores en **{liga_seleccionada}** que cumplan con los filtros.")
        else:
            st.warning("No se ha localizado la columna de valor de mercado en el archivo de Transfermarkt.")
    else:
        st.warning("No se han podido cargar los archivos desde la carpeta dataset_transfermarkt.")

# ==============================================================================
# SECCIÓN 3: SCOUTING Y PRODUCCIÓN OFENSIVA
# ==============================================================================
elif seccion_activa == "Scouting y Producción Ofensiva":
    st.subheader("Scouting de Talentos y Cuartiles de Mercado")
    st.markdown("Filtra jugadores jóvenes, analiza su producción ofensiva ajustada y compárala con los cuartiles históricos de la liga seleccionada.")

    edad_max = st.sidebar.slider("Edad Máxima", 17, 35, 23, step=1, key="edad_max_p1")
    presupuesto_max = st.sidebar.slider("Presupuesto Máximo (€)", 500000, 50000000, 5000000, step=500000, key="presupuesto_p1")
    minutos_min = st.sidebar.number_input("Minutos mínimos jugados (Temporada 25/26)", value=2000, step=100, key="minutos_p1")

    st.sidebar.markdown("---")
    filtrar_contrato = st.sidebar.checkbox("Filtrar por año de fin de contrato", value=False, key="filtro_contrato_p1")
    if filtrar_contrato:
        anio_contrato_max = st.sidebar.selectbox("Terminan contrato hasta el año:", [2026, 2027, 2028, 2029, 2030], index=1, key="anio_contrato_p1")
    else:
        anio_contrato_max = 2030

    ligas_disponibles_p1 = {
        'España (La Liga - ES1)': 'ES1', 
        'Inglaterra (Premier League - GB1)': 'GB1', 
        'Italia (Serie A - IT1)': 'IT1', 
        'Alemania (Bundesliga - L1)': 'L1', 
        'Francia (Ligue 1 - FR1)': 'FR1', 
        'Portugal (Primeira Liga - PO1)': 'PO1'
    }
    liga_sel_nombre = st.sidebar.selectbox("Liga de Análisis de Cuartiles", list(ligas_disponibles_p1.keys()), key="liga_sel_p1")
    liga_objetivo = ligas_disponibles_p1[liga_sel_nombre]

    demarcacion_sel = st.sidebar.selectbox("Demarcación", ['Centre-Forward', 'Left Winger', 'Right Winger', 'Attacking Midfield'], key="demarcacion_p1")

    @st.cache_data
    def cargar_datos_p1(liga_filtro):
        extract_dir = 'dataset_transfermarkt'
        try:
            import duckdb
            con = duckdb.connect(':memory:')
            
            query_historicos = f"""
            WITH Ultimas10Temporadas AS (
                SELECT DISTINCT season
                FROM read_csv_auto('{extract_dir}/games.csv')
                WHERE competition_id = '{liga_filtro}'
                ORDER BY season DESC
                LIMIT 10
            )
            SELECT c.name
            FROM read_csv_auto('{extract_dir}/clubs.csv') c
            JOIN read_csv_auto('{extract_dir}/games.csv') g ON c.club_id = g.home_club_id
            WHERE g.competition_id = '{liga_filtro}' 
            AND g.season IN (SELECT season FROM Ultimas10Temporadas)
            GROUP BY c.name
            HAVING COUNT(DISTINCT g.season) = 10
            """
            df_historicos = con.execute(query_historicos).df()
            clubes_historicos = df_historicos['name'].tolist()

            query = f"""
            WITH UltimoValor AS (
                SELECT player_id, market_value_in_eur
                FROM read_csv_auto('{extract_dir}/player_valuations.csv')
                QUALIFY ROW_NUMBER() OVER(PARTITION BY player_id ORDER BY date DESC) = 1
            ),
            EstadisticasTemporadas AS (
                SELECT 
                    player_id,
                    SUM(CASE WHEN date BETWEEN '2025-07-01' AND '2026-06-30' THEN minutes_played ELSE 0 END) AS min_25_26,
                    SUM(CASE WHEN date BETWEEN '2025-07-01' AND '2026-06-30' THEN goals ELSE 0 END) AS goles_25_26,
                    SUM(CASE WHEN date BETWEEN '2025-07-01' AND '2026-06-30' THEN assists ELSE 0 END) AS asis_25_26
                FROM read_csv_auto('{extract_dir}/appearances.csv')
                WHERE date BETWEEN '2025-07-01' AND '2026-06-30'
                GROUP BY player_id
            )
            SELECT 
                p.player_id, 
                p.name AS nombre, 
                p.date_of_birth AS fecha_nacimiento, 
                p.position AS posicion, 
                p.sub_position AS sub_posicion,
                p.foot AS pie_dominante,        
                p.height_in_cm AS altura_cm,    
                p.contract_expiration_date AS fin_contrato, 
                c.domestic_competition_id AS liga, 
                c.name AS club, 
                v.market_value_in_eur AS valor_mercado, 
                e.* EXCLUDE(player_id)
            FROM read_csv_auto('{extract_dir}/players.csv') p
            JOIN UltimoValor v ON p.player_id = v.player_id
            JOIN EstadisticasTemporadas e ON p.player_id = e.player_id
            LEFT JOIN read_csv_auto('{extract_dir}/clubs.csv') c ON p.current_club_id = c.club_id
            WHERE v.market_value_in_eur IS NOT NULL
            """
            df_1 = con.execute(query).df()
            df_1['fecha_nacimiento'] = pd.to_datetime(df_1['fecha_nacimiento'])
            fecha_referencia = pd.to_datetime('2026-06-30')
            df_1['edad'] = np.floor((fecha_referencia - df_1['fecha_nacimiento']).dt.days / 365.25)
            return df_1, clubes_historicos
        except Exception as e:
            st.error(f"Error cargando datos de Transfermarkt: {e}")
            return pd.DataFrame(), []

    df_raw, clubes_historicos = cargar_datos_p1(liga_objetivo)

    if not df_raw.empty:
        df_jovenes = df_raw[df_raw['edad'] <= edad_max].copy()

        coeficientes_liga = {
            'ES1': 1.0, 'GB1': 1.0, 'IT1': 1.0, 'L1': 1.0, 
            'FR1': 0.85, 'PO1': 0.85, 'NL1': 0.85,          
            'BE1': 0.75, 'TR1': 0.75, 'SC1': 0.75          
        }
        df_jovenes['coef_dificultad'] = df_jovenes['liga'].map(coeficientes_liga).fillna(0.7)
        df_jovenes['Goles_Ajustados'] = (df_jovenes['goles_25_26'] * df_jovenes['coef_dificultad']).round(1)
        df_jovenes['Asist_Ajustadas'] = (df_jovenes['asis_25_26'] * df_jovenes['coef_dificultad']).round(1)
        df_jovenes['Produccion_Ajustada'] = df_jovenes['Goles_Ajustados'] + df_jovenes['Asist_Ajustadas']

        df_jovenes['año_contrato'] = pd.to_datetime(df_jovenes['fin_contrato'], errors='coerce').dt.year

        filtro_presupuesto = df_jovenes['valor_mercado'] <= presupuesto_max
        filtro_regularidad = df_jovenes['min_25_26'] >= minutos_min
        filtro_demarcacion = df_jovenes['sub_posicion'] == demarcacion_sel

        if filtrar_contrato:
            filtro_c = df_jovenes['año_contrato'] <= anio_contrato_max
            df_shortlist = df_jovenes[filtro_presupuesto & filtro_regularidad & filtro_demarcacion & filtro_c].copy()
        else:
            df_shortlist = df_jovenes[filtro_presupuesto & filtro_regularidad & filtro_demarcacion].copy()

        if not df_shortlist.empty:
            df_shortlist['goles_mas_asistencias_25_26'] = df_shortlist['goles_25_26'] + df_shortlist['asis_25_26']
            df_shortlist['goles_p90'] = ((df_shortlist['goles_25_26'] / df_shortlist['min_25_26']) * 90).round(2)
            df_shortlist = df_shortlist.sort_values(by=['goles_mas_asistencias_25_26', 'goles_p90'], ascending=[False, False])
            
            df_shortlist.rename(columns={
                'nombre': 'Nombre', 'edad': 'Edad', 'sub_posicion': 'Demarcación',
                'pie_dominante': 'Pie', 'altura_cm': 'Altura (cm)', 'fin_contrato': 'Fin Contrato',
                'club': 'Club', 'min_25_26': 'Min.', 'goles_25_26': 'Goles',
                'asis_25_26': 'Asist.', 'goles_p90': 'Goles p/90', 'valor_mercado': 'Valor Mercado (€)'
            }, inplace=True)
            top_gangas = df_shortlist.head(5)
        else:
            top_gangas = pd.DataFrame()

        laliga_pos = df_raw[(df_raw['liga'] == liga_objetivo) & 
                            (df_raw['sub_posicion'] == demarcacion_sel) & 
                            (df_raw['club'].isin(clubes_historicos))].copy()

        if not laliga_pos.empty:
            laliga_pos['produccion_total'] = laliga_pos['goles_25_26'] + laliga_pos['asis_25_26']
            etiquetas_cuartiles = ['Q1 (Bajo Coste)', 'Q2 (Media-Baja)', 'Q3 (Media-Alta)', 'Q4 (Élite)']
            laliga_pos['Cuartil_Mercado'] = pd.qcut(laliga_pos['valor_mercado'].rank(method='first'), q=4, labels=etiquetas_cuartiles)
            
            resumen_cuartiles = laliga_pos.groupby('Cuartil_Mercado', observed=False).agg(
                Precio_Min=('valor_mercado', 'min'),
                Precio_Max=('valor_mercado', 'max'),
                Goles_Media=('goles_25_26', 'mean'),
                Asis_Media=('asis_25_26', 'mean'),
                Prod_Media=('produccion_total', 'mean')
            ).reset_index()
            
            resumen_cuartiles['Rango Precio'] = resumen_cuartiles.apply(lambda x: f"{x['Precio_Min']/1e6:g}M€ - {x['Precio_Max']/1e6:g}M€", axis=1)
            resumen_cuartiles[['Goles_Media', 'Asis_Media', 'Prod_Media']] = resumen_cuartiles[['Goles_Media', 'Asis_Media', 'Prod_Media']].round(1)
            
            prod_q4 = resumen_cuartiles.loc[3, 'Prod_Media']
            prod_q3 = resumen_cuartiles.loc[2, 'Prod_Media']
            prod_q2 = resumen_cuartiles.loc[1, 'Prod_Media']
            prod_q1 = resumen_cuartiles.loc[0, 'Prod_Media']
            rango_q4 = resumen_cuartiles.loc[3, 'Rango Precio']
            rango_q3 = resumen_cuartiles.loc[2, 'Rango Precio']
            rango_q2 = resumen_cuartiles.loc[1, 'Rango Precio']
            rango_q1 = resumen_cuartiles.loc[0, 'Rango Precio']
        else:
            prod_q4 = prod_q3 = prod_q2 = prod_q1 = 0
            rango_q4 = rango_q3 = rango_q2 = rango_q1 = ""
            resumen_cuartiles = pd.DataFrame()

        col1, col2, col3 = st.columns(3)
        col1.metric("Jugadores Encontrados", len(df_shortlist))
        inversion_top5 = top_gangas['Valor Mercado (€)'].sum() if not top_gangas.empty else 0
        col2.metric("Inversión Total (Top 5)", f"{inversion_top5/1e6:.1f}M€")
        rendimiento_medio = top_gangas['Produccion_Ajustada'].mean() if not top_gangas.empty else 0
        col3.metric("Rendimiento Medio (Top 5)", f"{rendimiento_medio:.1f}")

        st.markdown("---")
        st.subheader(f"Radiografía del Mercado en {liga_sel_nombre} ({demarcacion_sel})")
        if not resumen_cuartiles.empty:
            st.dataframe(
                resumen_cuartiles[['Cuartil_Mercado', 'Rango Precio', 'Goles_Media', 'Asis_Media', 'Prod_Media']].rename(
                    columns={
                        'Cuartil_Mercado': 'Cuartil de Mercado', 
                        'Goles_Media': 'Goles Promedio', 
                        'Asis_Media': 'Asistencias Promedio', 
                        'Prod_Media': 'Producción Total Promedio'
                    }
                ),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No hay suficientes datos históricos para los cuartiles de esta liga y demarcación.")

        st.markdown("---")

        if top_gangas.empty:
            st.warning(f"No se encontraron gangas para {demarcacion_sel} con los filtros actuales.")
        else:
            st.subheader("Top 5 Talentos Encontrados")
            st.dataframe(top_gangas[['Nombre', 'Edad', 'Club', 'Demarcación', 'Produccion_Ajustada', 'Valor Mercado (€)', 'Fin Contrato']], use_container_width=True)

            st.subheader(f"Comparativa Visual: Rendimiento vs Umbrales Históricos ({liga_sel_nombre})")
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=[f"{row['Nombre']} ({row['Edad']} años - {row['Valor Mercado (€)']/1e6:g}M€)" for _, row in top_gangas.iterrows()],
                y=top_gangas['Goles_Ajustados'],
                name='Goles Ponderados',
                marker_color='#2c3e50',
                text=top_gangas['Goles_Ajustados'],
                textposition='inside'
            ))
            fig.add_trace(go.Bar(
                x=[f"{row['Nombre']} ({row['Edad']} años - {row['Valor Mercado (€)']/1e6:g}M€)" for _, row in top_gangas.iterrows()],
                y=top_gangas['Asist_Ajustadas'],
                name='Asistencias Ponderadas',
                marker_color='#e74c3c',
                text=top_gangas['Asist_Ajustadas'],
                textposition='inside'
            ))
            if not laliga_pos.empty:
                fig.add_hline(y=prod_q4, line_dash="dash", line_color="#c0392b", annotation_text=f"Q4 Élite: {prod_q4:.1f} | {rango_q4}", annotation_position="top left", annotation_yanchor="bottom")
                fig.add_hline(y=prod_q3, line_dash="dot", line_color="#e67e22", annotation_text=f"Q3: {prod_q3:.1f} | {rango_q3}", annotation_position="top left", annotation_yanchor="bottom")
                fig.add_hline(y=prod_q2, line_dash="dashdot", line_color="#f1c40f", annotation_text=f"Q2: {prod_q2:.1f} | {rango_q2}", annotation_position="top left", annotation_yanchor="bottom")
                fig.add_hline(y=prod_q1, line_dash="solid", line_color="#27ae60", annotation_text=f"Q1: {prod_q1:.1f} | {rango_q1}", annotation_position="top left", annotation_yanchor="bottom")

            fig.update_layout(
                barmode='stack',
                xaxis_tickangle=-15,
                height=650,
                margin=dict(t=50, l=50, r=50, b=100),
                legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
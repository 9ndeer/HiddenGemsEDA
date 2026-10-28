
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# -- CONFIGURACIÓN DE PÁGINA --
st.set_page_config(page_title="Scouting Hidden Gems Pro", layout="wide")
st.title("💎 Hidden Gems: Scouting Interactivo y Análisis de Mercado")

# -- MENÚ PRINCIPAL DE 4 APARTADOS (PESTAÑAS) --
pestana_1, pestana_2, pestana_3, pestana_4 = st.tabs([
    "1️⃣ Scouting & Producción Ofensiva", 
    "2️⃣ Análisis de Eficiencia y Tasa de Conversión", 
    "3️⃣ Solidez Defensiva y Recuperación", 
    "4️⃣ Matriz de Rentabilidad y Coste/Rendimiento"
])

# ==========================================
# APARTADO 1: PANTALLA PRINCIPAL ORIGINAL
# ==========================================
with pestana_1:
    st.subheader("1️⃣ Scouting de Talentos y Cuartiles de Mercado")
    st.markdown("Filtra jugadores jóvenes, analiza su producción ofensiva ajustada y compárala con los cuartiles históricos de la liga seleccionada.")

    # -- 1. BARRA LATERAL (Filtros interactivos avanzados) --
    st.sidebar.header("Filtros de Búsqueda y Configuración")

    # Selector de Edad Máxima
    edad_max = st.sidebar.slider("Edad Máxima", 17, 35, 23, step=1, key="edad_max_p1")

    # Selector de Presupuesto
    presupuesto_max = st.sidebar.slider("Presupuesto Máximo (€)", 500000, 50000000, 5000000, step=500000, key="presupuesto_p1")

    # Selector de Minutos mínimos
    minutos_min = st.sidebar.number_input("Minutos mínimos jugados (Temporada 25/26)", value=2000, step=100, key="minutos_p1")

    # Selector de Fin de Contrato
    st.sidebar.markdown("---")
    st.sidebar.subheader("⏳ Filtrar por Fin de Contrato")
    filtrar_contrato = st.sidebar.checkbox("Filtrar por año de fin de contrato", value=False, key="filtro_contrato_p1")
    if filtrar_contrato:
        anio_contrato_max = st.sidebar.selectbox("Terminan contrato hasta el año:", [2026, 2027, 2028, 2029, 2030], index=1, key="anio_contrato_p1")
    else:
        anio_contrato_max = 2030

    # Selector de Ligas
    ligas_disponibles = {
        'España (La Liga - ES1)': 'ES1', 
        'Inglaterra (Premier League - GB1)': 'GB1', 
        'Italia (Serie A - IT1)': 'IT1', 
        'Alemania (Bundesliga - L1)': 'L1', 
        'Francia (Ligue 1 - FR1)': 'FR1', 
        'Portugal (Primeira Liga - PO1)': 'PO1'
    }
    liga_sel_nombre = st.sidebar.selectbox("Liga de Análisis de Cuartiles", list(ligas_disponibles.keys()), key="liga_sel_p1")
    liga_objetivo = ligas_disponibles[liga_sel_nombre]

    demarcacion_sel = st.sidebar.selectbox("Demarcación", ['Centre-Forward', 'Left Winger', 'Right Winger', 'Attacking Midfield'], key="demarcacion_p1")

    # -- 2. CARGA DE DATOS --
    @st.cache_data
    def cargar_datos(liga_filtro):
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
            st.error(f"Error cargando datos: Verifica que la carpeta 'dataset_transfermarkt' existe y tiene los archivos CSV. Error: {e}")
            return pd.DataFrame(), []

    df_raw, clubes_historicos = cargar_datos(liga_objetivo)

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

        # KPIs
        col1, col2, col3 = st.columns(3)
        col1.metric("Jugadores Encontrados", len(df_shortlist))
        inversion_top5 = top_gangas['Valor Mercado (€)'].sum() if not top_gangas.empty else 0
        col2.metric("Inversión Total (Top 5)", f"{inversion_top5/1e6:.1f}M€")
        rendimiento_medio = top_gangas['Produccion_Ajustada'].mean() if not top_gangas.empty else 0
        col3.metric("Rendimiento Medio (Top 5)", f"{rendimiento_medio:.1f}")

        st.markdown("---")
        st.subheader(f"📊 Radiografía del Mercado en {liga_sel_nombre} ({demarcacion_sel})")
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
            st.subheader("💎 Top 5 Hidden Gems Encontradas")
            st.dataframe(top_gangas[['Nombre', 'Edad', 'Club', 'Demarcación', 'Produccion_Ajustada', 'Valor Mercado (€)', 'Fin Contrato']], use_container_width=True)

            st.subheader(f"📈 Comparativa Visual: Rendimiento vs Umbrales Históricos ({liga_sel_nombre})")
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


# ==========================================
# APARTADO 3: SOLIDEZ DEFENSIVA Y RECUPERACIÓN
# ==========================================
with pestana_3:
    st.subheader("3️⃣ Solidez Defensiva y Recuperación de Balón")
    st.markdown("Apartado dedicado al análisis de perfiles defensivos, recuperaciones exitosas, intercepciones y duelos ganados evaluados mediante cuartiles defensivos.")
    st.info("🚧 Apartado en desarrollo. Próximamente incluirá métricas defensivas avanzadas y mapas de solidez por club.")

# ==========================================
# APARTADO 4: MATRIZ DE RENTABILIDAD Y COSTE/RENDIMIENTO
# ==========================================
with pestana_4:
    st.subheader("4️⃣ Matriz de Rentabilidad y Coste / Rendimiento")
    st.markdown("Evaluación financiera orientada a descubrir qué futbolistas aportan mayor producción ofensiva y defensiva por cada millón de euros invertido en su valor de mercado.")
    st.info("🚧 Apartado en desarrollo. Próximamente incluirá matrices de dispersión coste-rendimiento y análisis de amortización de fichajes.")

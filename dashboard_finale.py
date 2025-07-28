import streamlit as st
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import os

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="Delitos PBA",
    layout="wide",
    page_icon="📊"
)

# ESTILO VISUAL PROFESIONAL Y ADAPTATIVO
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        background-color: #ffffff !important;
        color: #000000 !important;
        font-family: 'Segoe UI', sans-serif;
    }
    h1, h2, h3, .stMarkdown {
        color: #000000 !important;
    }
    .stPlotlyChart {
        border-radius: 12px;
        padding: 1rem;
        border: 2px solid #007ACC;
        background-color: #FAFAFA;
        box-shadow: 0px 0px 6px rgba(0,0,0,0.05);
    }
    footer, header, #MainMenu {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# CARGA DE DATOS
@st.cache_data
def cargar_datos():
    df = pd.read_csv("snic-departamentos-anual.csv", sep=";", encoding="utf-8", on_bad_lines="skip")
    return df[df["provincia_nombre"] == "Buenos Aires"]

df = cargar_datos()
ultimo_anio = df["anio"].max()

# TÍTULO
st.markdown("## Informe de Delitos en la Provincia de Buenos Aires")

# 1. EVOLUCIÓN ANUAL
st.markdown("### 1. Evolución anual de hechos delictivos")
evol = df.groupby("anio")["cantidad_hechos"].sum().reset_index()
fig1 = px.line(evol, x="anio", y="cantidad_hechos", markers=True,
               title="Hechos delictivos por año",
               template="simple_white",
               color_discrete_sequence=["#e63946"])
st.plotly_chart(fig1, use_container_width=True)

# 2. TOP 10 DEPARTAMENTOS
st.markdown("### 2. Top 10 departamentos con más delitos")
df_top = df[df["anio"] == ultimo_anio].groupby("departamento_nombre")["cantidad_hechos"].sum().nlargest(10).reset_index()
fig2 = px.bar(df_top, x="cantidad_hechos", y="departamento_nombre", orientation="h",
              title="Departamentos con más delitos",
              template="simple_white",
              color_discrete_sequence=["#d7263d"])
st.plotly_chart(fig2, use_container_width=True)

# 3. TORTA POR TIPO DE DELITO
st.markdown("### 3. Principales tipos de delito")
df_tipo = df[df["anio"] == ultimo_anio].groupby("codigo_delito_snic_nombre")["cantidad_hechos"].sum().nlargest(10).reset_index()
fig3 = px.pie(df_tipo, values="cantidad_hechos", names="codigo_delito_snic_nombre",
              title="Top 10 tipos de delito",
              color_discrete_sequence=px.colors.sequential.Reds)
st.plotly_chart(fig3, use_container_width=True)

# 4. EVOLUCIÓN EN DEPARTAMENTOS
st.markdown("### 4. Evolución en los departamentos más afectados")
top10_nombres = df.groupby("departamento_nombre")["cantidad_hechos"].sum().nlargest(10).index
df_evol = df[df["departamento_nombre"].isin(top10_nombres)]
df_evol = df_evol.groupby(["anio", "departamento_nombre"])["cantidad_hechos"].sum().reset_index()
fig4 = px.line(df_evol, x="anio", y="cantidad_hechos", color="departamento_nombre",
               title="Evolución anual por departamento",
               template="simple_white",
               color_discrete_sequence=px.colors.qualitative.Set1)
st.plotly_chart(fig4, use_container_width=True)

# 5. MAPA DE CALOR POR CANTIDAD ABSOLUTA
st.markdown("### 5. Mapa de calor de delitos (cantidad absoluta)")
map_data = df[df["anio"] == ultimo_anio].groupby("departamento_nombre")["cantidad_hechos"].sum().reset_index()

geolocator = Nominatim(user_agent="pba_mapa")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

@st.cache_data
def obtener_coords(df_dep):
    coords_file = "coordenadas_departamentos.csv"
    if os.path.exists(coords_file):
        coords = pd.read_csv(coords_file)
        return df_dep.merge(coords, on="departamento_nombre", how="inner")

    def get_coords(nombre):
        try:
            loc = geocode(f"{nombre}, Buenos Aires, Argentina")
            if loc:
                return pd.Series({"lat": loc.latitude, "lon": loc.longitude})
        except:
            pass
        return pd.Series({"lat": None, "lon": None})

    coords = df_dep["departamento_nombre"].apply(get_coords)
    df_coords = pd.concat([df_dep, coords], axis=1).dropna(subset=["lat", "lon"])
    df_coords[["departamento_nombre", "lat", "lon"]].to_csv(coords_file, index=False)
    return df_coords

df_geo = obtener_coords(map_data)

fig5 = px.scatter_mapbox(
    df_geo,
    lat="lat",
    lon="lon",
    size="cantidad_hechos",
    color="cantidad_hechos",
    size_max=60,
    zoom=5.5,
    color_continuous_scale="Reds",
    hover_name="departamento_nombre",
    hover_data={"cantidad_hechos": True},
    height=700,
    title="Cantidad de delitos por departamento"
)
fig5.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":40,"l":0,"b":0})
st.plotly_chart(fig5, use_container_width=True)
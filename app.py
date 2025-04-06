import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

# Configuração do app
st.set_page_config(page_title="AllSpark OSP", layout="wide")
st.title("🔌 AllSpark OSP")

# Carregar lista de cidades
caminho_cidades = os.path.join("bases", "cidades.csv")
df_cidades = pd.read_csv(caminho_cidades, sep=';')
#st.write("Colunas do cidades.csv:", df_cidades.columns.tolist())

ufs = df_cidades["UF"].unique()
uf_selecionada = st.selectbox("Selecione o Estado (UF)", sorted(ufs))

municipios_filtrados = df_cidades[df_cidades["UF"] == uf_selecionada]["MUNICIPIO"].unique()
municipio_selecionado = st.selectbox("Selecione o Município", sorted(municipios_filtrados))

# Caminho dinâmico com nome do município
municipio_folder = municipio_selecionado.upper().replace(" ", "_")  # opcional: formatar nome do diretório
caminho_cto = os.path.join("bases", "INVENTORY", "CABOS", municipio_folder, "cto.csv")
if not os.path.exists(caminho_cto):
    st.warning(f"Arquivo não encontrado: {caminho_cto}")
    st.stop()

df_cto = pd.read_csv(caminho_cto, sep=';')

# Força os dados para float, substituindo vírgulas
df_cto['LATITUDE'] = df_cto['LATITUDE'].astype(str).str.replace(',', '.').astype(float)
df_cto['LONGITUDE'] = df_cto['LONGITUDE'].astype(str).str.replace(',', '.').astype(float)

cto_selecionada = st.selectbox("Digite ou selecione a CTO", df_cto["CTO_NAME"].unique())

# Verifica se já foi processado
if "processado" not in st.session_state:
    st.session_state.processado = False

if st.button("📍 Processar e gerar mapa"):
    cto_info = df_cto[df_cto["CTO_NAME"] == cto_selecionada]
    
    if not cto_info.empty:
        lat = cto_info.iloc[0]["LATITUDE"]
        lon = cto_info.iloc[0]["LONGITUDE"]

        st.session_state.lat = lat
        st.session_state.lon = lon
        st.session_state.cto_nome = cto_selecionada
        st.session_state.processado = True
    else:
        st.error("CTO não encontrada!")

# Se já foi processado, mostra o mapa
if st.session_state.get("processado", False):
    lat = st.session_state.lat
    lon = st.session_state.lon
    cto_nome = st.session_state.cto_nome

    st.success(f"CTO {cto_nome} localizada em ({lat}, {lon})")

    mapa = folium.Map(location=[lat, lon], zoom_start=17)
    folium.Marker([lat, lon], popup=f"CTO: {cto_nome}").add_to(mapa)

    st_folium(mapa, width=700, height=500)

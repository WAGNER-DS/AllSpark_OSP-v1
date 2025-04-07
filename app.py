import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
from folium.plugins import Draw, Fullscreen
from folium import LayerControl



st.set_page_config(page_title="AllSpark OSP", layout="wide")
from PIL import Image

img = Image.open("allspark2.png")
st.image(img, width=1600)  # ou outro valor que fique bom pra você

# Carregar lista de cidades
caminho_cidades = os.path.join("bases", "cidades.csv")
df_cidades = pd.read_csv(caminho_cidades, sep=';')

ufs = df_cidades["UF"].unique()
uf_selecionada = st.selectbox("Selecione o Estado (UF)", sorted(ufs))

municipios_filtrados = df_cidades[df_cidades["UF"] == uf_selecionada]["MUNICIPIO"].unique()
municipio_selecionado = st.selectbox("Selecione o Município", sorted(municipios_filtrados))

# Caminho para o arquivo de CTOs do município
municipio_folder = municipio_selecionado.upper().replace(" ", "_")
caminho_cto = os.path.join("bases", "INVENTORY", "CABOS", municipio_folder, "cto.csv")

if not os.path.exists(caminho_cto):
    st.warning(f"Arquivo não encontrado: {caminho_cto}")
    st.stop()

# Carregar dados da CTO
df_cto = pd.read_csv(caminho_cto, sep=';')
df_cto['LATITUDE'] = df_cto['LATITUDE'].astype(str).str.replace(',', '.').astype(float)
df_cto['LONGITUDE'] = df_cto['LONGITUDE'].astype(str).str.replace(',', '.').astype(float)

cto_selecionada = st.selectbox("Digite ou selecione a CTO", df_cto["CTO_NAME"].unique())

# Campo para distância OTDR
distancia_otdr = st.text_input("📏 Distância Medida OTDR (m)", placeholder="Digite somente números")
if distancia_otdr and not distancia_otdr.isdigit():
    st.warning("Por favor, digite apenas números inteiros.")

# Inicializar variáveis de sessão
if "processado" not in st.session_state:
    st.session_state.processado = False
if "cto_info" not in st.session_state:
    st.session_state.cto_info = None
if "lat" not in st.session_state:
    st.session_state.lat = None
if "lon" not in st.session_state:
    st.session_state.lon = None
if "cto_nome" not in st.session_state:
    st.session_state.cto_nome = None

# Botão para processar
if st.button("📍 Processar e gerar mapa"):
    cto_info = df_cto[df_cto["CTO_NAME"] == cto_selecionada]
    if not cto_info.empty:
        lat = cto_info.iloc[0]["LATITUDE"]
        lon = cto_info.iloc[0]["LONGITUDE"]

        st.session_state.lat = lat
        st.session_state.lon = lon
        st.session_state.cto_nome = cto_selecionada
        st.session_state.cto_info = cto_info
        st.session_state.processado = True
    else:
        st.error("CTO não encontrada!")

# Exibe as informações e o mapa
if st.session_state.processado and st.session_state.cto_info is not None:
    cto_info = st.session_state.cto_info
    lat = st.session_state.lat
    lon = st.session_state.lon
    cto_nome = st.session_state.cto_nome

    st.subheader("📌 Informações da CTO Selecionada")
    st.markdown(f"""
    - **UID_EQUIP:** `{cto_info.iloc[0]['UID_EQUIP']}`
    - **CTO_NAME:** `{cto_info.iloc[0]['CTO_NAME']}`
    - **MODELO:** `{cto_info.iloc[0]['MODELO']}`
    - **ARMARIO:** `{cto_info.iloc[0]['ARMARIO']}`
    - **ENDERECO:** `{cto_info.iloc[0]['ENDERECO']}`
    - **TIPO_CTO:** `{cto_info.iloc[0]['TIPO_CTO']}`
    - **SP:** `{cto_info.iloc[0]['SP']}`
    - **SS:** `{cto_info.iloc[0]['SS']}`  
    st.markdown(f"""
- Traçar rota no Google Maps: <a href="https://www.google.com/maps/dir/?api=1&destination={lat},{lon}" target="_self" rel="noopener noreferrer">Abrir no Google Maps</a>
""", unsafe_allow_html=True)


    


    # Criar o mapa com múltiplas camadas
    mapa = folium.Map(location=[lat, lon], zoom_start=17, control_scale=True)

    # Camadas extras
    folium.TileLayer("OpenStreetMap", name="Padrão").add_to(mapa)
    folium.TileLayer("CartoDB positron", name="Claro").add_to(mapa)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite',
        name='Google Satélite',
        overlay=False,
        control=True
    ).add_to(mapa)

    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google Hybrid',
        name='Google Hybrid',
        overlay=False,
        control=True
    ).add_to(mapa)

    # Adiciona marcador da CTO
    folium.Marker(
        location=[lat, lon],
        popup=f"CTO: {cto_nome}",
        icon=folium.Icon(icon="glyphicon glyphicon-screenshot", color="blue")
    ).add_to(mapa)

    # Plugin Draw (ferramenta para desenhar)
    Draw(export=True, filename='meu_desenho.geojson').add_to(mapa)

    # Plugin para tela cheia
    Fullscreen(position="topright").add_to(mapa)

    # Controle de camadas
    LayerControl(collapsed=False).add_to(mapa)
    st_folium(mapa, width=900, height=600)


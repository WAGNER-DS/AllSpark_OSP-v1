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

# UID da CTO selecionada
uid_cto = df_cto.iloc[0]["UID_EQUIP"]

# Caminhos dos arquivos de cabo
caminho_primarios = os.path.join("bases", "INVENTORY", "CABOS", municipio_folder, "cabos_primarios_group.csv")
caminho_secundarios = os.path.join("bases", "INVENTORY", "CABOS",  municipio_folder,"cabos_secundarios_group.csv")

# Inicializa variáveis de distância
distancia_primario = 0
distancia_secundario = 0

# Lista de UID de CEOS conectados à CTO
uid_ceos = []

# Carrega e filtra cabos secundários (CEOS → CTO)
if os.path.exists(caminho_secundarios):
    df_sec = pd.read_csv(caminho_secundarios, sep='|')
    sec_filtrado = df_sec[df_sec["UID_EQUIPAMENTO_Z"] == uid_cto]
    distancia_secundario = sec_filtrado["COMPRIMENTO_GEOMETRICO"].sum()
    uid_ceos = sec_filtrado["UID_EQUIPAMENTO_A"].unique().tolist()

# Carrega e filtra cabos primários (OLT → CEOS)
if os.path.exists(caminho_primarios) and uid_ceos:
    df_prim = pd.read_csv(caminho_primarios, sep='|')
    prim_filtrado = df_prim[df_prim["UID_EQUIPAMENTO_Z"].isin(uid_ceos)]
    distancia_primario = prim_filtrado["COMPRIMENTO_GEOMETRICO"].sum()



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
    
    - **Distância OTDR informada:** `{distancia_otdr if distancia_otdr.isdigit() else 'N/A'} m`
    - **Distância CEOS → CTO (secundário):** `{distancia_secundario:.2f} m`
    - **Distância OLT → CEOS (primário):** `{distancia_primario:.2f} m`
    """)


    # Total
    distancia_total = distancia_primario + distancia_secundario

    # HTML dinâmico com estilização
    html_diagrama = f"""
    <div style="text-align: center; font-family: Arial, sans-serif; margin-top: 30px;">
        <div style="display: flex; align-items: center; justify-content: center; gap: 10px; font-weight: bold;">
            <div style="background-color: #1f4e79; color: white; padding: 10px 20px; border-radius: 5px;">OLT</div>
            <div style="flex-grow:1; border-top: 5px solid red; position: relative;">
                <span style="position: absolute; top: -25px; left: 50%; transform: translateX(-50%); color: red;">{distancia_primario:.0f} m</span>
            </div>
            <div style="border: 2px solid black; padding: 10px 15px; border-radius: 3px;">SPL<br>1º Nível</div>
            <div style="flex-grow:1; border-top: 5px solid #003f5c; position: relative;">
                <span style="position: absolute; top: -25px; left: 50%; transform: translateX(-50%); color: #003f5c;">{distancia_secundario:.0f} m</span>
            </div>
            <div style="background-color: green; color: white; padding: 10px 20px; border-radius: 50%;">CTO</div>
        </div>
        <div style="margin-top: 20px; font-weight: bold;">
            📏 Distância Total (OLT → CTO): {distancia_total:.0f} m
        </div>
    </div>
    """

    # Exibe no Streamlit
    st.markdown(html_diagrama, unsafe_allow_html=True)



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

    popup_html = f"""
    <b>CTO:</b> {cto_nome}<br>
    <a href="https://www.google.com/maps/dir/?api=1&destination={lat},{lon}" target="_blank">
    🗺️ Traçar rota até a CTO no Google Maps
    </a>
    """

    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_html, max_width=300),
        icon=folium.Icon(icon="glyphicon glyphicon-screenshot", color="blue")
    ).add_to(mapa)


    # Plugin Draw (ferramenta para desenhar)
    Draw(export=True, filename='meu_desenho.geojson').add_to(mapa)

    # Plugin para tela cheia
    Fullscreen(position="topright").add_to(mapa)

    # Controle de camadas
    LayerControl(collapsed=False).add_to(mapa)
    st_folium(mapa, width=900, height=600)
    # Mostrar resultado dos filtros no app
    st.subheader("📋 Cabos Secundários (CEOS → CTO)")
    if not sec_filtrado.empty:
        st.dataframe(sec_filtrado)
    else:
        st.info("Nenhum cabo secundário encontrado para essa CTO.")

    st.subheader("📋 Cabos Primários (OLT → CEOS)")
    if not prim_filtrado.empty:
        st.dataframe(prim_filtrado)
    else:
        st.info("Nenhum cabo primário correspondente aos CEOS foi encontrado.")



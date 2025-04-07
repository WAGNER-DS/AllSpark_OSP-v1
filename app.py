import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
from folium.plugins import Draw, Fullscreen
from folium import LayerControl
from PIL import Image
from math import atan2, cos, sin
import folium
from folium.plugins import Draw, Fullscreen
import os
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
from geopy.distance import geodesic


# Configurações iniciais
st.set_page_config(page_title="AllSpark OSP", layout="wide")

# Logo
img = Image.open("allspark2.png")
st.image(img, width=1600)

# Inicialização segura de session_state
for key, default in {
    "processado": False,
    "cto_info": None,
    "lat": None,
    "lon": None,
    "cto_nome": None
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# Carregar lista de cidades
caminho_cidades = os.path.join("bases", "cidades.csv")
df_cidades = pd.read_csv(caminho_cidades, sep=';')
ufs = df_cidades["UF"].unique()
uf_selecionada = st.selectbox("Selecione o Estado (UF)", sorted(ufs))
municipios_filtrados = df_cidades[df_cidades["UF"] == uf_selecionada]["MUNICIPIO"].unique()
municipio_selecionado = st.selectbox("Selecione o Município", sorted(municipios_filtrados))
# Carregar CTOs
municipio_folder = municipio_selecionado.upper().replace(" ", "_")
caminho_cto = os.path.join("bases", "INVENTORY", "CABOS", municipio_folder, "cto.csv")
if not os.path.exists(caminho_cto):
    st.warning(f"Arquivo não encontrado: {caminho_cto}")
    st.stop()

df_cto = pd.read_csv(caminho_cto, sep=';')
df_cto['LATITUDE'] = df_cto['LATITUDE'].astype(str).str.replace(',', '.').astype(float)
df_cto['LONGITUDE'] = df_cto['LONGITUDE'].astype(str).str.replace(',', '.').astype(float)
cto_selecionada = st.selectbox("Digite ou selecione a CTO", df_cto["CTO_NAME"].unique())

# Distância OTDR
distancia_otdr = st.text_input("📏 Distância Medida OTDR (m)", placeholder="Digite somente números")
if distancia_otdr and not distancia_otdr.isdigit():
    st.warning("Por favor, digite apenas números inteiros.")

# Botão de processar
if st.button("📍 Processar e gerar mapa"):
    cto_info = df_cto[df_cto["CTO_NAME"] == cto_selecionada]
    if not cto_info.empty:
        st.session_state.lat = cto_info.iloc[0]["LATITUDE"]
        st.session_state.lon = cto_info.iloc[0]["LONGITUDE"]
        st.session_state.cto_nome = cto_selecionada
        st.session_state.cto_info = cto_info
        st.session_state.processado = True
    else:
        st.error("CTO não encontrada!")
# Se processado, mostrar dados e mapa
if st.session_state.processado and st.session_state.cto_info is not None:
    cto_info = st.session_state.cto_info
    lat = st.session_state.lat
    lon = st.session_state.lon
    cto_nome = st.session_state.cto_nome
    uid_cto = cto_info.iloc[0]["UID_EQUIP"]

    # Caminhos dos cabos
    caminho_primarios = os.path.join("bases", "INVENTORY", "CABOS", municipio_folder, "cabos_primarios_group.csv")
    caminho_secundarios = os.path.join("bases", "INVENTORY", "CABOS", municipio_folder, "cabos_secundarios_group.csv")

    distancia_primario = 0
    distancia_secundario = 0
    uid_ceos = []
    sec_filtrado = pd.DataFrame()
    prim_filtrado = pd.DataFrame()

    if os.path.exists(caminho_secundarios):
        df_sec = pd.read_csv(caminho_secundarios, sep='|')
        sec_filtrado = df_sec[df_sec["UID_EQUIPAMENTO_Z"] == uid_cto]
        distancia_secundario = sec_filtrado["COMPRIMENTO_GEOMETRICO"].sum()
        uid_ceos = sec_filtrado["UID_EQUIPAMENTO_A"].unique().tolist()

    if os.path.exists(caminho_primarios) and uid_ceos:
        df_prim = pd.read_csv(caminho_primarios, sep='|')
        prim_filtrado = df_prim[df_prim["UID_EQUIPAMENTO_Z"].isin(uid_ceos)]
        distancia_primario = prim_filtrado["COMPRIMENTO_GEOMETRICO"].sum()

    # Mostrar informações da CTO
    st.subheader("📌 Informações da CTO Selecionada")
    st.markdown(f"""
    - **UID_EQUIP:** `{uid_cto}`
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


    # Diagrama visual
    distancia_total = distancia_primario + distancia_secundario
    import streamlit.components.v1 as components
    html_diagrama = f"""
    <div style="text-align: center; font-family: Arial, sans-serif; margin-top: 30px;">
        <!-- Linha principal do diagrama -->
        <div style="display: flex; align-items: center; justify-content: center; gap: 10px; font-weight: bold; margin-bottom: 10px;">
            <div style="background-color: #1f4e79; color: white; padding: 10px 20px; border-radius: 5px;">OLT</div>

            <div style="flex-grow:1; height: 5px; background-color: red; position: relative;">
                <span style="position: absolute; top: -20px; left: 50%; transform: translateX(-50%); color: red;">
                    {f"{distancia_primario:,.0f}".replace(",", ".")} m
                </span>
            </div>

            <div style="border: 2px solid black; padding: 10px 15px; border-radius: 3px;">SPL<br>1º Nível</div>

            <div style="flex-grow:1; height: 5px; background-color: #003f5c; position: relative;">
                <span style="position: absolute; top: -20px; left: 50%; transform: translateX(-50%); color: #003f5c;">
                    {f"{distancia_secundario:,.0f}".replace(",", ".")} m
                </span>
            </div>

            <div style="background-color: green; color: white; padding: 10px 20px; border-radius: 50%;">CTO</div>
        </div>

        <!-- Apenas o texto da distância total -->
        <div style="margin-top: 10px; font-weight: bold; color: #0074D9;">
            📏 Distância Total (OLT → CTO): {f"{distancia_total:,.0f}".replace(",", ".")} m
        </div>
    </div>
    """

    components.html(html_diagrama, height=180)
    # Função para deslocar uma linha lateralmente (offset)
    # Mapa interativo
    from math import atan2, sin, cos
    def encontrar_ponto_por_distancia(coord_list, distancia_m):
        acumulado = 0
        for i in range(len(coord_list) - 1):
            ponto_atual = coord_list[i]
            proximo_ponto = coord_list[i + 1]
            dist = geodesic(ponto_atual, proximo_ponto).meters
            if acumulado + dist >= distancia_m:
                # Proporção entre o ponto atual e o próximo
                restante = distancia_m - acumulado
                proporcao = restante / dist
                lat = ponto_atual[0] + proporcao * (proximo_ponto[0] - ponto_atual[0])
                lon = ponto_atual[1] + proporcao * (proximo_ponto[1] - ponto_atual[1])
                return (lat, lon)
            acumulado += dist
        return coord_list[-1]  # Se a distância for maior que o trajeto

    # Função para deslocar uma linha (usado quando há duplicação de traçado)
    def deslocar_linha(lat1, lon1, lat2, lon2, offset):
        angle = atan2(lat2 - lat1, lon2 - lon1)
        perp_angle = angle + (3.1416 / 2)
        dlat = offset * sin(perp_angle)
        dlon = offset * cos(perp_angle)
        return [(lat1 + dlat, lon1 + dlon), (lat2 + dlat, lon2 + dlon)]
    
    def deslocar_linha_com_conexao(lat1, lon1, lat2, lon2, offset=0.00003):
        from math import atan2, sin, cos

        # Ângulo da linha
        angle = atan2(lat2 - lat1, lon2 - lon1)
        perp_angle = angle + (3.1416 / 2)

        # Deslocamento lateral
        dlat = offset * sin(perp_angle)
        dlon = offset * cos(perp_angle)

        # Pontos com deslocamento apenas no meio (início e fim reais)
        mid1 = (lat1 + (lat2 - lat1) * 0.25 + dlat, lon1 + (lon2 - lon1) * 0.25 + dlon)
        mid2 = (lat1 + (lat2 - lat1) * 0.75 + dlat, lon1 + (lon2 - lon1) * 0.75 + dlon)

        return [(lat1, lon1), mid1, mid2, (lat2, lon2)]

    
    mapa = folium.Map(location=[lat, lon], zoom_start=17, control_scale=True)

    # 1. Não colocar nenhuma camada base com show=True
    folium.TileLayer("OpenStreetMap", name="Padrão").add_to(mapa)

    # 3. Adiciona outras camadas de imagem depois (Satélite etc.)
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
    # 2. Adiciona a camada "Claro" por último (ela será a principal)
    folium.TileLayer("CartoDB positron", name="Claro").add_to(mapa)


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

    caminho_tracados = os.path.join("bases", "INVENTORY", "CABOS", municipio_folder, "cabos_tracados.csv")

    if os.path.exists(caminho_tracados):
        df_tracados = pd.read_csv(caminho_tracados, sep='|')

        # 🎯 Filtrar os cabos conectados à CTO
        ids_sec = sec_filtrado["IDENTIFICADOR_UNICO_CABO_CONECTADO"].dropna().unique().tolist()
        df_sec = df_tracados[df_tracados["IDENTIFICADOR_UNICO_CABO"].isin(ids_sec)].copy()
        df_sec["origem"] = "sec"

        ids_prim = prim_filtrado["IDENTIFICADOR_UNICO_CABO_CONECTADO"].dropna().unique().tolist()
        df_prim = df_tracados[df_tracados["IDENTIFICADOR_UNICO_CABO"].isin(ids_prim)].copy()
        df_prim["origem"] = "prim"

        # 🔁 Concatenar os dados e criar uma chave única para cada traçado
        df_all = pd.concat([df_sec, df_prim], ignore_index=True)
        df_all["chave_tracado"] = df_all["UUID_LOCAL_TRACADO_INICIAL"].astype(str) + "_" + df_all["UUID_LOCAL_TRACADO_FINAL"].astype(str)
        chaves_duplicadas = df_all["chave_tracado"].duplicated(keep=False)

        # Criar camadas separadas
        camada_prim = folium.FeatureGroup(name="Cabos Primários", show=True)
        camada_sec = folium.FeatureGroup(name="Cabos Secundários", show=True)

        # Desenhar os cabos nas respectivas camadas
        for _, row in df_all.iterrows():
            try:
                lat1 = float(str(row["LATITUDE_INICIAL"]).replace(',', '.'))
                lon1 = float(str(row["LONGITUDE_INICIAL"]).replace(',', '.'))
                lat2 = float(str(row["LATITUDE_FINAL"]).replace(',', '.'))
                lon2 = float(str(row["LONGITUDE_FINAL"]).replace(',', '.'))

                # Verifica se precisa aplicar deslocamento
                offset = 0
                if row["origem"] == "prim" and row["chave_tracado"] in df_all[chaves_duplicadas]["chave_tracado"].values:
                    coords = deslocar_linha_com_conexao(lat1, lon1, lat2, lon2, offset=0.00001)
                else:
                    coords = [(lat1, lon1), (lat2, lon2)]

                # Define a cor por tipo
                cor = 'red' if row["origem"] == "prim" else '#003f5c'

                polyline = folium.PolyLine(
                    locations=coords,
                    color=cor,
                    weight=4,
                    opacity=0.85,
                    tooltip=f"Cabo: {row['IDENTIFICADOR_UNICO_CABO']}"
                )

                if row["origem"] == "prim":
                    polyline.add_to(camada_prim)
                else:
                    polyline.add_to(camada_sec)

            except Exception as e:
                st.warning(f"Erro ao desenhar cabo: {e}")
    camada_prim.add_to(mapa)
    camada_sec.add_to(mapa)

    # Desenho interativo com Folium
    Draw(export=True, filename='meu_desenho.geojson').add_to(mapa)
    Fullscreen(position="topright").add_to(mapa)
    LayerControl(collapsed=False).add_to(mapa)

    st_folium(mapa, use_container_width=True, height=600)

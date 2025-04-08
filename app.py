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
if st.button("📍 Processar e TraceBack"):
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
                cor = 'purple' if row["origem"] == "prim" else 'Blue'

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

######################################################################################
###  BLOCO DE DESENHO UNICO DO CABO secudario ##################################################
######################################################################################

# Função para ordenar blocos de segmentos encadeados com inversão automática
# Mesma função de ordenação
    from collections import defaultdict

    # Mapear o sequenciamento para cada cabo conectado
    mapa_sequenciamento = sec_filtrado.set_index('IDENTIFICADOR_UNICO_CABO_CONECTADO')['SEQUENCIAMENTO_DO_ENCAMINHAMENTO'].to_dict()

    # Construir dicionário com chave = sequenciamento, valor = lista de segmentos [[p1],[p2]]
    dict_segmentos = defaultdict(list)

    for _, row in df_sec.iterrows():
        cabo_id = row['IDENTIFICADOR_UNICO_CABO']
        seq = mapa_sequenciamento.get(cabo_id, None)
        if seq is None:
            continue  # Ignora se não encontrar sequenciamento

        lat1 = float(str(row['LATITUDE_INICIAL']).replace(',', '.'))
        lon1 = float(str(row['LONGITUDE_INICIAL']).replace(',', '.'))
        lat2 = float(str(row['LATITUDE_FINAL']).replace(',', '.'))
        lon2 = float(str(row['LONGITUDE_FINAL']).replace(',', '.'))

        dict_segmentos[int(seq)].append([[lat1, lon1], [lat2, lon2]])

    def ordenar_blocos_encadeados(dict_segmentos, ponto_inicial):
        caminho_total = [ponto_inicial]
        for sequencia in sorted(dict_segmentos.keys(), reverse=True):
            segmentos = dict_segmentos[sequencia].copy()
            caminho = []

            while segmentos:
                encontrou = False
                for i, seg in enumerate(segmentos):
                    p1 = tuple(seg[0])
                    p2 = tuple(seg[1])
                    if not caminho:
                        if caminho_total[-1] == p1:
                            caminho.append(p1)
                            caminho.append(p2)
                            segmentos.pop(i)
                            encontrou = True
                            break
                        elif caminho_total[-1] == p2:
                            caminho.append(p2)
                            caminho.append(p1)
                            segmentos.pop(i)
                            encontrou = True
                            break
                    else:
                        if caminho[-1] == p1:
                            caminho.append(p2)
                            segmentos.pop(i)
                            encontrou = True
                            break
                        elif caminho[-1] == p2:
                            caminho.append(p1)
                            segmentos.pop(i)
                            encontrou = True
                            break
                        elif caminho[0] == p1:
                            caminho.insert(0, p2)
                            segmentos.pop(i)
                            encontrou = True
                            break
                        elif caminho[0] == p2:
                            caminho.insert(0, p1)
                            segmentos.pop(i)
                            encontrou = True
                            break

                if not encontrou:
                    break  # 🔒 Para evitar loop infinito se não conseguir conectar

            # 🔒 Adiciona apenas se conseguiu construir um caminho
            if caminho:
                if caminho_total[-1] == caminho[0]:
                    caminho_total += caminho[1:]
                else:
                    caminho_total += caminho
            else:
                print(f"Aviso: Bloco {sequencia} não foi conectado ao caminho total.")

        return caminho_total
    # Encontrar o maior sequenciamento (último bloco do caminho)
    maior_seq = max(dict_segmentos.keys())

    # Pegar o último segmento dentro do maior sequenciamento
    segmento_final = dict_segmentos[maior_seq][-1]  # último segmento do maior bloco

    # Usar o ponto inicial do segmento como ponto de partida
    ponto_inicial = tuple(segmento_final[0])

    # Verificar o ponto inicial escolhido
    #with st.expander("📍 Ponto inicial utilizado para ordenar"):
    #    st.write(ponto_inicial)


    # Gerar linha ordenada
    linha_secundaria_ordenada = ordenar_blocos_encadeados(dict_segmentos, ponto_inicial)

    # Adicionar camada ao mapa
    camada_ordenada = folium.FeatureGroup(name="Caminho Secundário (CEOS → CTO)", show=False)

    folium.PolyLine(
        locations=linha_secundaria_ordenada,
        color="yellow",
        weight=5,
        opacity=1,
        tooltip="Caminho ordenado CEOS → CTO"
    ).add_to(camada_ordenada)

    camada_ordenada.add_to(mapa)


######################################################################################
######################################################################################
    from collections import defaultdict
    def ordenar_blocos_encadeados_crescente(dict_segmentos, ponto_inicial):
        caminho_total = [ponto_inicial]

        for sequencia in sorted(dict_segmentos.keys()):  # ← sem reverse
            segmentos = dict_segmentos[sequencia].copy()
            caminho = []

            while segmentos:
                encontrou = False
                for i, seg in enumerate(segmentos):
                    p1 = tuple(seg[0])
                    p2 = tuple(seg[1])

                    if not caminho:
                        if caminho_total[-1] == p1:
                            caminho.append(p1)
                            caminho.append(p2)
                            segmentos.pop(i)
                            encontrou = True
                            break
                        elif caminho_total[-1] == p2:
                            caminho.append(p2)
                            caminho.append(p1)
                            segmentos.pop(i)
                            encontrou = True
                            break
                    else:
                        if caminho[-1] == p1:
                            caminho.append(p2)
                            segmentos.pop(i)
                            encontrou = True
                            break
                        elif caminho[-1] == p2:
                            caminho.append(p1)
                            segmentos.pop(i)
                            encontrou = True
                            break
                        elif caminho[0] == p1:
                            caminho.insert(0, p2)
                            segmentos.pop(i)
                            encontrou = True
                            break
                        elif caminho[0] == p2:
                            caminho.insert(0, p1)
                            segmentos.pop(i)
                            encontrou = True
                            break

                if not encontrou:
                    break

            # Combina o caminho se conseguir conectar
            if caminho:
                if caminho_total[-1] == caminho[0]:
                    caminho_total += caminho[1:]
                else:
                    caminho_total += caminho
            else:
                print(f"Aviso: Bloco {sequencia} não conectado ao caminho total.")

        return caminho_total

    # Filtrar UID_EQUIPAMENTO_A dos cabos secundários conectados à CTO selecionada
    uid_ceos = sec_filtrado["UID_EQUIPAMENTO_A"].dropna().unique().tolist()

    # Carregar cabos primários e filtrar pelos UID_CEOS
    df_prim = pd.read_csv(caminho_primarios, sep='|')
    prim_filtrado = df_prim[df_prim["UID_EQUIPAMENTO_Z"].isin(uid_ceos)].copy()

    # Carregar os traçados dos cabos primários
    ids_prim = prim_filtrado["IDENTIFICADOR_UNICO_CABO_CONECTADO"].dropna().unique().tolist()
    df_prim_tracado = df_tracados[df_tracados["IDENTIFICADOR_UNICO_CABO"].isin(ids_prim)].copy()

    # Mapeamento: IDENTIFICADOR_UNICO_CABO → SEQUENCIAMENTO_DO_ENCAMINHAMENTO
    mapa_seq_prim = prim_filtrado.set_index('IDENTIFICADOR_UNICO_CABO_CONECTADO')['SEQUENCIAMENTO_DO_ENCAMINHAMENTO'].to_dict()

    # Criar dicionário de segmentos encadeados para os cabos primários
    dict_segmentos_prim = defaultdict(list)

    for _, row in df_prim_tracado.iterrows():
        cabo_id = row['IDENTIFICADOR_UNICO_CABO']
        seq = mapa_seq_prim.get(cabo_id, None)
        if seq is None:
            continue

        lat1 = float(str(row['LATITUDE_INICIAL']).replace(',', '.'))
        lon1 = float(str(row['LONGITUDE_INICIAL']).replace(',', '.'))
        lat2 = float(str(row['LATITUDE_FINAL']).replace(',', '.'))
        lon2 = float(str(row['LONGITUDE_FINAL']).replace(',', '.'))

        dict_segmentos_prim[int(seq)].append([[lat1, lon1], [lat2, lon2]])

    # 📍 Determinar ponto inicial (do primeiro segmento do menor sequenciamento)
    menor_seq = min(dict_segmentos_prim.keys())
    primeiro_segmento = dict_segmentos_prim[menor_seq][0]
    ponto_inicial_prim = tuple(primeiro_segmento[0])  # 🟢 ponto de partida correto

    # 📏 Gerar caminho encadeado na ordem crescente (OLT → CEOS)
    caminho_primario = ordenar_blocos_encadeados_crescente(dict_segmentos_prim, ponto_inicial_prim)

    # 🔴 Exibir caminho primário no mapa
    camada_prim_ordenada = folium.FeatureGroup(name="Caminho Primário (OLT → CEOS)", show=False)

    folium.PolyLine(
        locations=caminho_primario,
        color="red",
        weight=5,
        opacity=1,
        tooltip="Cabo Primário Único"
    ).add_to(camada_prim_ordenada)

    camada_prim_ordenada.add_to(mapa)

    # (opcional) debug visual no Streamlit
    #with st.expander("📍 Caminho Primário (OLT → CEOS)"):
    ##    st.write(f"Início: {caminho_primario[0]}")
    #    st.write(f"Fim: {caminho_primario[-1]}")
    #    st.code(caminho_primario)


    # Inverter caminho primário (para garantir sentido OLT → CEOS)
    #caminho_primario = caminho_primario[::-1]

    
    # Concatenar os dois caminhos
    if caminho_primario[-1] == linha_secundaria_ordenada[0]:
        caminho_total = caminho_primario + linha_secundaria_ordenada[1:]
    else:
        caminho_total = caminho_primario + linha_secundaria_ordenada

    # Criar camada única com o caminho completo OLT → CTO
    camada_total = folium.FeatureGroup(name="Caminho OTDR (OLT → CTO)", show=False)

    folium.PolyLine(
        locations=caminho_total,
        color="orange",
        weight=6,
        opacity=1,
        tooltip="Caminho Total OTDR (Primário + Secundário)"
    ).add_to(camada_total)

    # Marcadores de início e fim
    #folium.Marker(
    #    location=caminho_total[0],
    #    tooltip="🔵 Início (OLT)",
    #    icon=folium.Icon(color='green')
    #).add_to(camada_total)

    #folium.Marker(
    #    location=caminho_total[-1],
    #    tooltip="🔴 Fim (CTO)",
    #    icon=folium.Icon(color='red')
    #).add_to(camada_total)

    # Adicionar ao mapa
    camada_total.add_to(mapa)

    from folium.plugins import AntPath

    # 🔁 Inverter o caminho para obter o trajeto CTO → OLT
    caminho_reverso = caminho_total[::-1]
    #caminho_reverso = caminho_total

    # ⚡ Determinar o ponto da falha com base na distância OTDR
    if distancia_otdr and distancia_otdr.isdigit():
        distancia_otdr_metros = int(distancia_otdr)
        ponto_falha = encontrar_ponto_por_distancia(caminho_reverso, distancia_otdr_metros)

        # 🔶 Camada reversa (CTO → ponto de falha)
        camada_falha = folium.FeatureGroup(name="Falha OTDR (CTO → OLT)", show=True)

        # Trajeto até o ponto de falha
        index_falha = None
        acumulado = 0
        for i in range(len(caminho_reverso) - 1):
            dist = geodesic(caminho_reverso[i], caminho_reverso[i + 1]).meters
            if acumulado + dist >= distancia_otdr_metros:
                index_falha = i
                break
            acumulado += dist

        if index_falha is not None:
            trajeto_falha = caminho_reverso[:index_falha + 1] + [ponto_falha]

            # 🚨 Linha animada com AntPath
            AntPath(
                locations=trajeto_falha,
                color='red',
                pulse_color='white',
                weight=5,
                opacity=0.8,
                tooltip="Rota até ponto de falha (CTO → OLT)"
            ).add_to(camada_falha)

            # ❌ Ponto de Falha com popup de rota
            link_rota = f"https://www.google.com/maps/dir/?api=1&destination={ponto_falha[0]},{ponto_falha[1]}"
            popup_html = f"""
            <b>📍 Ponto de Falha OTDR</b><br>
            <a href="{link_rota}" target="_blank">🗺️ Traçar rota até aqui no Google Maps</a>
            """

            folium.Marker(
                location=ponto_falha,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip="❌ Ponto de Falha OTDR",
                icon=folium.Icon(color='black', icon='remove', prefix='glyphicon')
            ).add_to(camada_falha)

            camada_falha.add_to(mapa)
        else:
            st.warning("Não foi possível localizar o ponto da falha na rota.")

    # Desenho interativo com Folium
    Draw(export=True, filename='meu_desenho.geojson').add_to(mapa)
    Fullscreen(position="topright").add_to(mapa)
    LayerControl(collapsed=False).add_to(mapa)

    st_folium(mapa, use_container_width=True, height=600)

    st.subheader("🧭 Coordenadas dos caminhos (debug)")

    #with st.expander("📍 Caminho Primário (OLT → CEOS)"):
    #    st.write(f"Início: {caminho_primario[0]}")
    #    st.write(f"Fim: {caminho_primario[-1]}")
    #    st.code(caminho_primario)

    #with st.expander("📍 Caminho Secundário (CEOS → CTO)"):
    #    st.write(f"Início: {linha_secundaria_ordenada[0]}")
    #    st.write(f"Fim: {linha_secundaria_ordenada[-1]}")
    #    st.code(linha_secundaria_ordenada)
    # ============================
    # 🔍 Camada: Segmentos Secundários (Brutos)
    # ============================
    #with st.expander("🔍 Segmentos Brutos por Sequenciamento"):
    #    for seq in sorted(dict_segmentos.keys(), reverse=True):
    #        st.markdown(f"**Sequenciamento {seq}**")
    #        for seg in dict_segmentos[seq]:
    #            st.code(seg)
    # ============================
    # 🔍 Camada: Segmentos Pri (Brutos)
    # ============================
    #with st.expander("🔍 Segmentos Brutos por Sequenciamento"):
    #    for seq in sorted(dict_segmentos.keys(), reverse=True):
    #        st.markdown(f"**Sequenciamento {seq}**")
    #        for seg in dict_segmentos[seq]:
    #            st.code(seg)



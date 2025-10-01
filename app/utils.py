import numpy as np
from datetime import datetime, timezone
import geopandas as gpd
from shapely.geometry import Point
import requests
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.distance import geodesic
import pandas as pd

from .config import OPENWEATHER_API_KEY

geolocator = Nominatim(user_agent="meu_app_previsao_enchente_sp")
geocode_reverso_com_delay = RateLimiter(geolocator.reverse, min_delay_seconds=1)

def get_neighbourhood(lat, lon):
    """
    Usa a geocodificação reversa para encontrar o bairro de um par de coordenadas.
    """
    try:
        location = geocode_reverso_com_delay((lat, lon), language='pt-br', exactly_one=True)

        if location:
            address = location.raw.get('address', {})
            bairro = address.get('suburb') or address.get('city_district') or address.get('neighbourhood')
            return bairro if bairro else "Bairro Desconhecido"
        else:
            return "Localização Não Encontrada"

    except Exception as e:
        print(f"Erro na geocodificação reversa: {e}")
        return
    

def analyze_floodable_sections(lat_evento, lon_evento, gdf_trechos_agua, raio_km=5):
    """
    Analisa os trechos de água vulneráveis num raio a partir de uma coordenada.

    Args:
        lat_evento (float): Latitude do ponto de interesse.
        lon_evento (float): Longitude do ponto de interesse.
        gdf_trechos_agua (GeoDataFrame): GeoDataFrame com todos os trechos vulneráveis.
        raio_km (int): Raio da busca em quilômetros.

    Returns:
        dict: Um dicionário com as features calculadas.
    """

    # Dicionário de retorno padrão caso nenhum trecho seja encontrado
    features_padrao = {
        'n_trechos_vulneraveis_5km': 0,
        'n_trechos_alto_impacto_5km': 0,
        'risco_medio_trechos_5km': 0.0
    }

    try:
        # Cria um GeoDataFrame para o ponto de interesse
        ponto_interesse = gpd.GeoDataFrame(
            [1], geometry=[Point(lon_evento, lat_evento)], crs='EPSG:4326'
        )

        # Reprojeta os dados para um CRS métrico para o buffer
        trechos_agua_proj = gdf_trechos_agua.to_crs('EPSG:5880')
        ponto_proj = ponto_interesse.to_crs('EPSG:5880')

        # Cria o buffer (área circular)
        raio_em_metros = raio_km * 1000
        buffer_area = ponto_proj.geometry.buffer(raio_em_metros)

        # Filtra os trechos que intersectam o buffer usando sjoin
        trechos_no_raio = gdf_trechos_agua.sjoin(
            gpd.GeoDataFrame(geometry=buffer_area.to_crs(gdf_trechos_agua.crs)),
            how="inner",
            predicate="intersects"
        )

        if trechos_no_raio.empty:
            return features_padrao

        # --- Feature Engineering ---
        # 1. Contagem simples de trechos na área
        n_trechos = len(trechos_no_raio)

        # 2. Contagem de trechos de "Alto Impacto"
        n_alto_impacto = len(trechos_no_raio[trechos_no_raio['Impacto'] == 'Alto'])

        # 3. Score de Risco Médio
        mapeamento_risco = {"Baixo": 1, "Médio": 2, "Alto": 3}
        # Usamos .get(x, 0) para tratar valores não esperados sem erro
        score = (trechos_no_raio['Frequencia'].apply(lambda x: mapeamento_risco.get(x, 0)) +
                 trechos_no_raio['Impacto'].apply(lambda x: mapeamento_risco.get(x, 0)) +
                 trechos_no_raio['Vulnerabil'].apply(lambda x: mapeamento_risco.get(x, 0)))
        risco_medio = score.mean()

        return {
            'n_trechos_vulneraveis_5km': n_trechos,
            'n_trechos_alto_impacto_5km': n_alto_impacto,
            'risco_medio_trechos_5km': risco_medio
        }

    except Exception as e:
        print(f"Erro em analyze_floodable_sections: {e}")
        return features_padrao


# Adicione esta função à sua célula de funções
def analyze_local_relief(lat_evento, lon_evento, gdf_relevo):
    """
    Encontra a unidade de relevo para uma dada coordenada e extrai os atributos.

    Args:
        lat_evento (float): Latitude do ponto de interesse.
        lon_evento (float): Longitude do ponto de interesse.
        gdf_relevo (GeoDataFrame): GeoDataFrame com os polígonos do relevo.

    Returns:
        dict: Um dicionário com as features de relevo.
    """

    colunas_relevo = [
        'NIVEL_1', 'DECLIV_MED', 'AMPLIT_ALT',
        'DDREN_MED', 'E_HIDR_MED', 'GEOL_CPRM', 'GEOL_rev'
    ]

    # Dicionário padrão com valores nulos (ou 'Desconhecido') caso não encontre
    features_padrao = {col: np.nan for col in colunas_relevo}
    features_padrao['NIVEL_1'] = 'Desconhecido'
    features_padrao['GEOL_CPRM'] = 'Desconhecido'
    features_padrao['GEOL_rev'] = 'Desconhecido'

    try:
        # Cria o ponto a partir da coordenada
        ponto = Point(lon_evento, lat_evento)

        # Encontra o polígono de relevo que contém o ponto
        # A operação gdf.contains(ponto) retorna uma série booleana
        unidade_relevo = gdf_relevo[gdf_relevo.contains(ponto)]

        # Se não encontrar nenhum polígono, retorna o padrão
        if unidade_relevo.empty:
            return features_padrao

        # Se encontrou, pega a primeira (e única) linha
        dados_encontrados = unidade_relevo.iloc[0]

        # Extrai os valores das colunas de interesse para um dicionário
        features_extraidas = dados_encontrados[colunas_relevo].to_dict()

        return features_extraidas

    except Exception as e:
        print(f"Erro em analyze_local_relief: {e}")
        return features_padrao
    

def get_weather_forecast_24h(lat, lon):
    """Busca a previsão do tempo para as próximas 24 horas (em intervalos de 3h)."""
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=pt_br"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        forecast_data = {
            # "city_name": data['city']['name'],
            # "entries": [],
            "chuva_24h": 0.0,
            "intensidade_max_24h": 0.0
        }

        for item in data['list'][:8]:  # próximos 24h
            rain_3h = item.get('rain', {}).get('3h', 0.0)
            forecast_data['chuva_24h'] += rain_3h

            # Atualiza intensidade máxima se necessário
            if rain_3h > forecast_data['intensidade_max_24h']:
                forecast_data['intensidade_max_24h'] = rain_3h

            # forecast_data['entries'].append({
            #     "datetime_utc": datetime.fromtimestamp(item['dt'], timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
            #     "temp": item['main']['temp'],
            #     "description": item['weather'][0]['description'],
            #     "rain_3h": rain_3h,
            #     "pop": item.get('pop', 0)
            # })

        return forecast_data

    except requests.exceptions.RequestException as e:
        print(f"Erro ao chamar a API do OpenWeather (Forecast): {e}")
        return None
    

def accumulated_rain(lat_evento, lon_evento, datahora_ref, medidas, estacoes, chuva_prox_24h=0, k=5, p=2, max_dist_km=20):
    def idw_rain(inicio, fim):
        # Filtra medidas no período
        medidas_periodo = medidas[medidas["datahora"].between(inicio, fim)]
        chuva_estacoes = medidas_periodo.groupby("codEstacao")["valorMedida"].sum().reset_index()
        chuva_estacoes = chuva_estacoes.merge(estacoes, on="codEstacao", how="inner")

        # Calcula distâncias
        chuva_estacoes["dist"] = [
            geodesic((lat_evento, lon_evento), (float(str(lat).replace(",", ".")), float(str(lon).replace(",", ".")))).km
            for lat, lon in zip(chuva_estacoes["latitude"], chuva_estacoes["longitude"])
        ]

        # Filtra estações dentro do raio
        chuva_estacoes = chuva_estacoes[chuva_estacoes["dist"] <= max_dist_km]

        if chuva_estacoes.empty:
            return np.nan

        # Seleciona até k mais próximos
        vizinhos = chuva_estacoes.nsmallest(k, "dist")

        # Se tiver estação exatamente no ponto
        if any(vizinhos["dist"] == 0):
            return vizinhos.loc[vizinhos["dist"] == 0, "valorMedida"].values[0]

        # IDW
        vizinhos["valorMedida"] = pd.to_numeric(vizinhos["valorMedida"], errors="coerce")
        vizinhos = vizinhos.dropna(subset=["valorMedida"])

        weights = 1 / (vizinhos["dist"] ** p)
        return (vizinhos["valorMedida"] * weights).sum() / weights.sum()
    
    # Calcula acumulados
    chuva_24h = idw_rain(datahora_ref - pd.Timedelta(hours=24), datahora_ref)
    chuva_48h = idw_rain(datahora_ref - pd.Timedelta(hours=48), datahora_ref)

    print("Chuva 24h calculada:", chuva_24h)
    print("Chuva 48h calculada:", chuva_48h)

    # O valor de chuva 48 será as próximas 24h + as 24h anteriores
    # O valor de chuva 72 será as próximas 24h + as 48h anteriores
    return {"chuva_48h": chuva_24h + chuva_prox_24h, "chuva_72h": chuva_48h + chuva_prox_24h}


def consecutive_rainy_days(lat_evento, lon_evento, data_evento, medidas, estacoes, limiar_chuva=0.2, max_dias_verificar=30, k=5, p=2, max_dist_km=20):
    """
    Calcula o número de dias consecutivos com chuva acima de um limiar
    antes da data do evento.
    """
    dias_consecutivos = 0
    # Normaliza a data do evento para garantir que começamos a verificação a partir do dia anterior
    data_base = data_evento.normalize()

    def idw_rain(inicio, fim):
        # Filtra medidas no período
        medidas_periodo = medidas[medidas["datahora"].between(inicio, fim)]
        chuva_estacoes = medidas_periodo.groupby("codEstacao")["valorMedida"].sum().reset_index()
        chuva_estacoes = chuva_estacoes.merge(estacoes, on="codEstacao", how="inner")

        # Calcula distâncias
        chuva_estacoes["dist"] = [
            geodesic((lat_evento, lon_evento), (float(str(lat).replace(",", ".")), float(str(lon).replace(",", ".")))).km
            for lat, lon in zip(chuva_estacoes["latitude"], chuva_estacoes["longitude"])
        ]

        # Filtra estações dentro do raio
        chuva_estacoes = chuva_estacoes[chuva_estacoes["dist"] <= max_dist_km]

        if chuva_estacoes.empty:
            return np.nan

        # Seleciona até k mais próximos
        vizinhos = chuva_estacoes.nsmallest(k, "dist")

        # Se tiver estação exatamente no ponto
        if any(vizinhos["dist"] == 0):
            return vizinhos.loc[vizinhos["dist"] == 0, "valorMedida"].values[0]

        # IDW
        vizinhos["valorMedida"] = pd.to_numeric(vizinhos["valorMedida"], errors="coerce")
        vizinhos = vizinhos.dropna(subset=["valorMedida"])

        weights = 1 / (vizinhos["dist"] ** p)
        return (vizinhos["valorMedida"] * weights).sum() / weights.sum()

    # Loop para verificar os dias anteriores, até o limite de 'max_dias_verificar'
    for i in range(1, max_dias_verificar + 1):
        # Define a janela de 24h para o dia anterior que estamos verificando
        dia_verificar_fim = data_base - pd.Timedelta(days=i-1) - pd.Timedelta(seconds=1)
        dia_verificar_inicio = data_base - pd.Timedelta(days=i)

        # Usa a função chuva_idw para calcular o total de chuva nesse dia
        chuva_do_dia = idw_rain(dia_verificar_inicio, dia_verificar_fim,)

        # Se a chuva no dia for maior que o limiar, incrementa o contador
        if chuva_do_dia > limiar_chuva:
            dias_consecutivos += 1
        else:
            # Se não choveu, a sequência é quebrada, então paramos o loop
            break

    return dias_consecutivos
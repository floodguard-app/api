import numpy as np
import geopandas as gpd
from shapely.geometry import Point

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
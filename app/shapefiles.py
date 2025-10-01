import geopandas as gpd
from .config import SHAPEFILES

print("Carregando shapefiles...")

gdf_trechos_vulneraveis = gpd.read_file(SHAPEFILES["vulnerabilidade"])
print("Shapefile de trechos vulneráveis lido com sucesso.")

gdf_relevo_sp = gpd.read_file(SHAPEFILES["relevo"])
print("Shapefile de relevo lido com sucesso.")
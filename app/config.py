import os
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

SECRET_KEY = os.getenv("OPENWEATHER_API_KEY")

MODEL_PATH = "data/modelo.pkl"
SHAPEFILES = {
    "vulnerabilidade": "data/trechos_inundaveis.shp",
    "relevo": "data/UBC_v2.shp"
}
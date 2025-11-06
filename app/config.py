import os
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

MODEL_PATH = "data/modelo.joblib"
BAIRRO_ENCODER_PATH = "data/label_encoder_bairro.joblib"
SHAPEFILES = {
    "vulnerabilidade": "data/trechos_inundaveis.shp",
    "relevo": "data/UBC_v2.shp"
}
SHEETS = {
    "pluviometros": "data/pluviometrica_novembro.csv",
    "hidrologicas": "data/hidrologica_novembro.csv",
}
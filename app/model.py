import joblib
from .config import MODEL_PATH

print("Carregando modelo...")
model = joblib.load(MODEL_PATH)
print("Modelo carregado com sucesso.")
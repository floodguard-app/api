import joblib
from .config import MODEL_PATH, BAIRRO_ENCODER_PATH

print("Carregando modelo...")
model = joblib.load(MODEL_PATH)
print("Modelo carregado com sucesso.")

print("Carregando encoder...")
bairro_encoder = joblib.load(BAIRRO_ENCODER_PATH)
print("Encoder carregado com sucesso.")
import pandas as pd
from .config import SHEETS

medidas_pluviometros = pd.read_csv(SHEETS["pluviometros"], sep=";")
medidas_pluviometros["datahora"] = pd.to_datetime(medidas_pluviometros["datahora"], errors="coerce")
medidas_pluviometros.drop("uf", axis=1, inplace=True) # Todas as estações são de SP
estacoes_pluviometricas = medidas_pluviometros[["codEstacao", "latitude", "longitude", "nomeEstacao"]].drop_duplicates().reset_index(drop=True)

medidas_hidrologicas = pd.read_csv(SHEETS["hidrologicas"], sep=";")
medidas_hidrologicas['datahora'] = pd.to_datetime(medidas_hidrologicas['datahora'], errors='coerce')
medidas_hidrologicas.dropna(subset=['datahora'], inplace=True)
estacoes_hidrologicas = medidas_hidrologicas[["codEstacao", "latitude", "longitude", "nomeEstacao"]].drop_duplicates().reset_index(drop=True)


# class DadosMeteorologicos:
#     @property
#     def medidas_pluviometros(self):
#         df = pd.read_csv(SHEETS["pluviometros"], sep=";")
#         df["datahora"] = pd.to_datetime(df["datahora"], errors="coerce")
#         df.drop("uf", axis=1, inplace=True)
#         return df

#     @property
#     def estacoes_pluviometricas(self):
#         return self.medidas_pluviometros[["codEstacao", "latitude", "longitude", "nomeEstacao"]].drop_duplicates().reset_index(drop=True)

#     @property
#     def medidas_hidrologicas(self):
#         df = pd.read_csv(SHEETS["hidrologicas"], sep=";")
#         df["datahora"] = pd.to_datetime(df["datahora"], errors="coerce")
#         df.dropna(subset=["datahora"], inplace=True)
#         return df

#     @property
#     def estacoes_hidrologicas(self):
#         return self.medidas_hidrologicas[["codEstacao", "latitude", "longitude", "nomeEstacao"]].drop_duplicates().reset_index(drop=True)
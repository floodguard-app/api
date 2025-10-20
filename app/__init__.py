from flask import Flask, request, jsonify
from datetime import datetime
import pandas as pd
from .model import model, bairro_encoder
from .shapefiles import gdf_trechos_vulneraveis, gdf_relevo_sp
from .utils import get_neighbourhood, analyze_floodable_sections, analyze_local_relief, get_weather_forecast_24h, accumulated_rain, consecutive_rainy_days as get_consecutive_rainy_days, obter_nivel_rio_proximo, acumulado_ultimos_dias
# from .sheets import DadosMeteorologicos
from .sheets import medidas_pluviometros, estacoes_pluviometricas, medidas_hidrologicas, estacoes_hidrologicas

def create_app():
    app = Flask(__name__)

    @app.route("/status", methods=["GET"])
    def status():
        return jsonify({"status": "ok"})


    @app.route("/shapes", methods=["GET"])
    def shapes():
        return jsonify({
            "trechos_vulneraveis": len(gdf_trechos_vulneraveis),
            "relevo": len(gdf_relevo_sp)
        })
    
    
    @app.route("/floodable_stretches", methods=["GET"]) # Exemplo de uso: /floodable_stretches?lat=-23.55052&lon=-46.633308
    def floodable_stretches():
        try:
            lat = float(request.args.get("lat"))
            lon = float(request.args.get("lon"))

            response = analyze_floodable_sections(lat, lon, gdf_trechos_vulneraveis)
            return jsonify(response)
        except TypeError:
            return jsonify({"error": "Por favor, passe 'lat' e 'lon' na URL"}), 400
        except ValueError:
            return jsonify({"error": "Lat e Lon devem ser numeros"}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        

    @app.route("/local_relief", methods=["GET"]) # Exemplo de uso: /local_relief?lat=-23.55052&lon=-46.633308
    def local_relief():
        try:
            lat = float(request.args.get("lat"))
            lon = float(request.args.get("lon"))

            response = analyze_local_relief(lat, lon, gdf_relevo_sp)
            return jsonify(response)
        except TypeError:
            return jsonify({"error": "Por favor, passe 'lat' e 'lon' na URL"}), 400
        except ValueError:
            return jsonify({"error": "Lat e Lon devem ser numeros"}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500


    @app.route("/weather_forecast_24h", methods=["GET"])
    def weather_forecast_24h():
        try:
            lat = float(request.args.get("lat"))
            lon = float(request.args.get("lon"))

            response = get_weather_forecast_24h(lat, lon)
            if response is None:
                return jsonify({"error": "Erro ao obter a previsão do tempo"}), 500
            return jsonify(response)
        except TypeError:
            return jsonify({"error": "Por favor, passe 'lat' e 'lon' na URL"}), 400
        except ValueError:
            return jsonify({"error": "Lat e Lon devem ser numeros"}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
        
    @app.route("/consecutive_rainy_days", methods=["GET"])
    def consecutive_rainy_days():
        try:
            lat = float(request.args.get("lat"))
            lon = float(request.args.get("lon"))
            print("Recebido lat:", lat, "lon:", lon)
        except TypeError:
            return jsonify({"error": "Por favor, passe 'lat' e 'lon' na URL"}), 400
        except ValueError:
            return jsonify({"error": "Lat e Lon devem ser numeros"}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500

        try:
            data_atual = pd.Timestamp(datetime.now())
            response = get_consecutive_rainy_days(lat, lon, data_atual, medidas_pluviometros, estacoes_pluviometricas)
            if response is None:
                return jsonify({"error": "Erro ao obter dias chuvosos consecutivos"}), 500
            return jsonify(response)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
    
    @app.route("/neighbourhood", methods=["GET"]) # Exemplo de uso: /neighbourhood?lat=-23.55052&lon=-46.633308
    def neighbourhood():
        try:
            lat = float(request.args.get("lat"))
            lon = float(request.args.get("lon"))

            bairro = get_neighbourhood(lat, lon)
            if bairro is None:
                return jsonify({"error": "Erro ao obter o bairro"}), 500
            return jsonify({"bairro": bairro})
        except TypeError:
            return jsonify({"error": "Por favor, passe 'lat' e 'lon' na URL"}), 400
        except ValueError:
            return jsonify({"error": "Lat e Lon devem ser numeros"}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        

    @app.route("/accumulated_on_week", methods=["GET"]) # Exemplo de uso: /neighbourhood?lat=-23.55052&lon=-46.633308
    def accumulated_on_week():
        try:
            lat = float(request.args.get("lat"))
            lon = float(request.args.get("lon"))
        except TypeError:
            return jsonify({"error": "Por favor, passe 'lat' e 'lon' na URL"}), 400
        except ValueError:
            return jsonify({"error": "Lat e Lon devem ser numeros"}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500

        try:
            data_atual = pd.Timestamp(datetime.now())
            result = acumulado_ultimos_dias(lat, lon, data_atual, medidas_pluviometros, estacoes_pluviometricas, dias=7)

            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        

    @app.route("/predict", methods=["GET"])
    def predict():
        try:
            lat = float(request.args.get("lat"))
            lon = float(request.args.get("lon"))

            print("Recebido lat:", lat, "lon:", lon)
            
            data_atual = pd.Timestamp(datetime.now()) # data_evento
            neighbourhood = get_neighbourhood(lat, lon) # bairro
            try:
                neighbourhood = bairro_encoder.transform(["Vila Madalena"])[0]
                print("Bairro codificado:", neighbourhood)
            except ValueError as e:
                print(f"AVISO: Encontrado um bairro não visto no treino: {e}")
                neighbourhood = -1

            features_floodable = analyze_floodable_sections(lat, lon, gdf_trechos_vulneraveis) # n_trechos_alto_impacto_5km, n_trechos_vulneraveis_5km, risco_medio_trechos_5km
            features_relief = analyze_local_relief(lat, lon, gdf_relevo_sp) # AMPLIT_ALT, DDREN_MED, DECLIV_MED, E_HIDR_MED
            weather_forecast = get_weather_forecast_24h(lat, lon) # chuva_24h, intensidade_max_24h

            if weather_forecast is None:
                return jsonify({"error": "Erro ao obter a previsão do tempo"}), 500

            # TODO: preencher períodos sem informações
            consec_rain_days = get_consecutive_rainy_days(lat, lon, data_atual, medidas_pluviometros, estacoes_pluviometricas)

            features = {
                "bairro": neighbourhood,
                **features_floodable, 
                **features_relief, 
                **weather_forecast,
                "dias_consec_chuva": consec_rain_days,
            }

            # return jsonify(features)
            print("Features para predição:", features)

            feature_order = model.feature_names_in_
            X = pd.DataFrame([features], columns=feature_order)
            prediction = model.predict(X)
            probabilities = model.predict_proba(X)
            
            results = []
            for i, pred in enumerate(prediction):
                prob_flood = probabilities[i][1]
                result_text = 'RISCO DE ENCHENTE' if pred == 1 else 'SEM RISCO DE ENCHENTE'
                results.append((result_text, f"{prob_flood:.2%}"))

            return jsonify(results)
        except Exception as e:
            return jsonify({"error": str(e)}), 400
        

    @app.route("/test_predict", methods=["GET"])
    def test_predict():
        try:
            neighbourhood = bairro_encoder.transform(["Goianases"])[0]

            # 'bairro': ['Vila Madalena', 'Centro', 'Centro', 'Goianases', 'Glicério', 'Vila Leopoldina', 'Belém'],
            # 'chuva_24h': [42.5, 80.1, 0, 5.0, 15.3, 10, 2],
            # 'intensidade_max_24h': [7.0, 15.5, 0, 0.5, 2.1, 2, 0.1],
            # 'dias_consec_chuva': [6, 2, 0, 0, 1, 0, 1],
            # 'n_trechos_vulneraveis_5km': [1, 2, 2, 0, 4, 3, 8],
            # 'n_trechos_alto_impacto_5km': [1, 2, 2, 0, 4, 3, 8],
            # 'risco_medio_trechos_5km': [3.0, 3.0, 0, 0.0, 3.0, 3.0, 3.0],
            # 'DECLIV_MED': [8.24, 4.6,  4.6, 9.5, 12.5, 5.29, 3.97],
            # 'AMPLIT_ALT': [122.5, 83.9, 83.9, 150.0, 122.6, 58.63, 75.12],
            # 'E_HIDR_MED': [619.3, 695.0, 695.0, 450.1, 573.6, 596.9, 894.1],
            # 'DDREN_MED': [3.9, 10.2, 10.2, 6.5, 10.8, 10.2, 20.9]

            features = {
                "bairro": neighbourhood,
                "AMPLIT_ALT": 150.0,
                "DDREN_MED": 6.5,
                "DECLIV_MED": 9.5,
                "E_HIDR_MED": 450.1,
                "chuva_24h": 5.0,
                "dias_consec_chuva": 0,
                "intensidade_max_24h": 0.5,
                "n_trechos_alto_impacto_5km": 0,
                "n_trechos_vulneraveis_5km": 0,
                "risco_medio_trechos_5km": 0.0
            }

            # return jsonify(features)
            print("Features para predição:", features)

            feature_order = model.feature_names_in_
            X = pd.DataFrame([features], columns=feature_order)
            prediction = model.predict(X)
            probabilities = model.predict_proba(X)
            
            results = []
            for i, pred in enumerate(prediction):
                prob_flood = probabilities[i][1]
                result_text = 'RISCO DE ENCHENTE' if pred == 1 else 'SEM RISCO DE ENCHENTE'
                results.append((result_text, f"{prob_flood:.2%}"))

            return jsonify(results)
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    return app
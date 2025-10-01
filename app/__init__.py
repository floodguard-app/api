from flask import Flask, request, jsonify
from .model import model
from .shapefiles import gdf_trechos_vulneraveis, gdf_relevo_sp
from .utils import get_neighbourhood, analyze_floodable_sections, analyze_local_relief, get_weather_forecast_24h
from datetime import datetime

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
        

    @app.route("/predict", methods=["GET"])
    def predict():
        try:
            # PRECISO DE:
            # data_evento	bairro	chuva_24h	chuva_48h	chuva_72h	intensidade_max_24h	dias_consec_chuva	nivel_rio_24h	n_trechos_vulneraveis_5km	n_trechos_alto_impacto_5km	risco_medio_trechos_5km	NIVEL_1	DECLIV_MED	AMPLIT_ALT	DDREN_MED	E_HIDR_MED	GEOL_CPRM	GEOL_rev
            
            # FALTAM:
            # chuva_48h	chuva_72h	dias_consec_chuva	nivel_rio_24h

            lat = float(request.args.get("lat"))
            lon = float(request.args.get("lon"))
            
            data_atual = datetime.now().strftime("%Y-%m-%d") # data_evento
            neighbourhood = get_neighbourhood(lat, lon) # bairro
            features_floodable = analyze_floodable_sections(lat, lon, gdf_trechos_vulneraveis) # n_trechos_alto_impacto_5km, n_trechos_vulneraveis_5km, risco_medio_trechos_5km
            features_relief = analyze_local_relief(lat, lon, gdf_relevo_sp) # AMPLIT_ALT, DDREN_MED, DECLIV_MED, E_HIDR_MED, GEOL_CPRM, GEOL_rev, NIVEL_1
            weather_forecast = get_weather_forecast_24h(lat, lon) # chuva_24h, intensidade_max_24h

            if weather_forecast is None:
                return jsonify({"error": "Erro ao obter a previsão do tempo"}), 500
            
            features = {
                "data_evento": data_atual, 
                "bairro": neighbourhood,
                **features_floodable, 
                **features_relief, 
                **weather_forecast
            }

            return jsonify(features)
            # prediction = model.predict([features])
            # return jsonify({"prediction": prediction.tolist()})
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    return app
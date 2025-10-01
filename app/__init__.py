from flask import Flask, request, jsonify
from .model import model
from .shapefiles import gdf_trechos_vulneraveis, gdf_relevo_sp
from .utils import analyze_floodable_sections, analyze_local_relief

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
    
    # Exemplo de uso:
    # /floodable_stretches?lat=-23.55052&lon=-46.633308
    @app.route("/floodable_stretches", methods=["GET"])
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
        
    # Exemplo de uso:
    # /local_relief?lat=-23.55052&lon=-46.633308
    @app.route("/local_relief", methods=["GET"])
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


    # @app.route("/predict", methods=["POST"])
    # def predict():
    #     try:
    #         data = request.get_json()
    #         features = data["features"]

    #         prediction = model.predict([features])
    #         return jsonify({"prediction": prediction.tolist()})
    #     except Exception as e:
    #         return jsonify({"error": str(e)}), 400

    return app
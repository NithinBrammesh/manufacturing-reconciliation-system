from flask import Flask, jsonify
from flask_cors import CORS
import redis

app = Flask(__name__)
CORS(app)

r = redis.Redis(
    host="redis",
    port=6379,
    decode_responses=True
)

@app.route("/api/reconciliation", methods=["GET"])
def get_reconciliation():

    metrics = r.hgetall(
        "reconciliation_metrics"
    )

    if not metrics:
        metrics = {
            "total_aoi": 0,
            "total_spi": 0,
            "matched": 0,
            "missing_in_spi": 0,
            "missing_in_aoi": 0,
            "aoi_match_percentage": 0,
            "aoi_loss_percentage": 0,
            "spi_match_percentage": 0,
            "spi_loss_percentage": 0,
            "overall_percentage": 0
        }

    return jsonify(metrics)

@app.route("/")
def home():
    return jsonify({
        "status": "running",
        "service": "Manufacturing Reconciliation API"
    })

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
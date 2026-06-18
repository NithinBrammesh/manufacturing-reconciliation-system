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

    metrics = r.hgetall("reconciliation_metrics")

    if not metrics:

        metrics = {

            # ============================================
            # TOTAL RECORDS
            # ============================================

            "total_aoi": 0,
            "total_spi": 0,
            "total_fcr": 0,

            # ============================================
            # AOI ↔ SPI
            # ============================================

            "aoi_spi_matched": 0,
            "aoi_missing_in_spi": 0,
            "spi_missing_in_aoi": 0,

            "aoi_spi_match_percentage": 0,
            "aoi_spi_loss_percentage": 0,

            "spi_aoi_match_percentage": 0,
            "spi_aoi_loss_percentage": 0,

            # ============================================
            # AOI ↔ FCR
            # ============================================

            "aoi_fcr_matched": 0,
            "aoi_missing_in_fcr": 0,
            "fcr_missing_in_aoi": 0,

            "aoi_fcr_match_percentage": 0,
            "aoi_fcr_loss_percentage": 0,

            "fcr_aoi_match_percentage": 0,
            "fcr_aoi_loss_percentage": 0,

            # ============================================
            # SPI ↔ FCR
            # ============================================

            "spi_fcr_matched": 0,
            "spi_missing_in_fcr": 0,
            "fcr_missing_in_spi": 0,

            "spi_fcr_match_percentage": 0,
            "spi_fcr_loss_percentage": 0,

            "fcr_spi_match_percentage": 0,
            "fcr_spi_loss_percentage": 0,

            # ============================================
            # OVERALL
            # ============================================

            "all_matched": 0,
            "overall_total": 0,
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
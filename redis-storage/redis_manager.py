import redis
import json


class RedisManager:

    def __init__(self):

        self.redis_client = redis.Redis(
            host="localhost",
            port=6379,
            db=0,
            decode_responses=True
        )

    # ============================
    # SPI
    # ============================

    def save_spi_barcode(self, barcode):

        self.redis_client.sadd(
            "spi_barcodes",
            barcode
        )

    def get_spi_barcodes(self):

        return self.redis_client.smembers(
            "spi_barcodes"
        )

    # ============================
    # AOI
    # ============================

    def save_aoi_barcode(self, barcode):

        self.redis_client.sadd(
            "aoi_barcodes",
            barcode
        )

    def get_aoi_barcodes(self):

        return self.redis_client.smembers(
            "aoi_barcodes"
        )

    # ============================
    # Reconciliation Summary
    # ============================

    def save_reconciliation_report(
        self,
        report
    ):

        self.redis_client.set(
            "reconciliation_report",
            json.dumps(report)
        )

    def get_reconciliation_report(self):

        data = self.redis_client.get(
            "reconciliation_report"
        )

        if data:
            return json.loads(data)

        return {}

    # ============================
    # Cleanup
    # ============================

    def clear_spi_data(self):

        self.redis_client.delete(
            "spi_barcodes"
        )

    def clear_aoi_data(self):

        self.redis_client.delete(
            "aoi_barcodes"
        )

    def clear_all(self):

        self.clear_spi_data()
        self.clear_aoi_data()

        self.redis_client.delete(
            "reconciliation_report"
        )


# ============================
# Testing
# ============================

if __name__ == "__main__":

    redis_manager = RedisManager()

    redis_manager.save_spi_barcode(
        "SPI123"
    )

    redis_manager.save_aoi_barcode(
        "AOI123"
    )

    print(
        redis_manager.get_spi_barcodes()
    )

    print(
        redis_manager.get_aoi_barcodes()
    )
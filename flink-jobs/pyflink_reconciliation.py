import json
import redis

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.watermark_strategy import WatermarkStrategy
from pyflink.datastream.connectors.kafka import KafkaSource
from pyflink.datastream.connectors.kafka import KafkaOffsetsInitializer

print("Starting Manufacturing Reconciliation Job...")

# =====================================================
# FLINK ENVIRONMENT
# =====================================================

env = StreamExecutionEnvironment.get_execution_environment()
env.set_parallelism(1)

# =====================================================
# REDIS CONNECTION
# =====================================================

startup_redis = redis.Redis(
    host="redis",
    port=6379,
    decode_responses=True
)

# Uncomment if you want fresh metrics every restart

startup_redis.delete("aoi_barcodes")
startup_redis.delete("spi_barcodes")
startup_redis.delete("reconciliation_metrics")

print("Redis reconciliation data cleared")

# =====================================================
# METRICS CALCULATION
# =====================================================

def update_metrics(r):

    aoi_set = set(r.smembers("aoi_barcodes"))
    spi_set = set(r.smembers("spi_barcodes"))

    matched = aoi_set.intersection(spi_set)

    missing_in_spi = aoi_set - spi_set
    missing_in_aoi = spi_set - aoi_set

    total_aoi = len(aoi_set)
    total_spi = len(spi_set)

    matched_count = len(matched)

    missing_spi_count = len(missing_in_spi)
    missing_aoi_count = len(missing_in_aoi)

    aoi_match_percentage = (
        (matched_count / total_aoi) * 100
        if total_aoi > 0 else 0
    )

    aoi_loss_percentage = (
        (missing_spi_count / total_aoi) * 100
        if total_aoi > 0 else 0
    )

    spi_match_percentage = (
        (matched_count / total_spi) * 100
        if total_spi > 0 else 0
    )

    spi_loss_percentage = (
        (missing_aoi_count / total_spi) * 100
        if total_spi > 0 else 0
    )

    overall_percentage = (
        (matched_count / max(total_aoi, total_spi)) * 100
        if max(total_aoi, total_spi) > 0 else 0
    )

    r.hset(
        "reconciliation_metrics",
        mapping={
            "total_aoi": total_aoi,
            "total_spi": total_spi,
            "matched": matched_count,
            "missing_in_spi": missing_spi_count,
            "missing_in_aoi": missing_aoi_count,
            "aoi_match_percentage": round(aoi_match_percentage, 2),
            "aoi_loss_percentage": round(aoi_loss_percentage, 2),
            "spi_match_percentage": round(spi_match_percentage, 2),
            "spi_loss_percentage": round(spi_loss_percentage, 2),
            "overall_percentage": round(overall_percentage, 2)
        }
    )

# =====================================================
# AOI KAFKA SOURCE
# =====================================================

aoi_source = (
    KafkaSource.builder()
    .set_bootstrap_servers("kafka:9092")
    .set_topics("aoi-topic")
    .set_group_id("aoi-group")
    .set_starting_offsets(KafkaOffsetsInitializer.earliest())
    .set_value_only_deserializer(SimpleStringSchema())
    .build()
)

# =====================================================
# SPI KAFKA SOURCE
# =====================================================

spi_source = (
    KafkaSource.builder()
    .set_bootstrap_servers("kafka:9092")
    .set_topics("spi-topic")
    .set_group_id("spi-group")
    .set_starting_offsets(KafkaOffsetsInitializer.earliest())
    .set_value_only_deserializer(SimpleStringSchema())
    .build()
)

# =====================================================
# CREATE STREAMS
# =====================================================

aoi_stream = env.from_source(
    aoi_source,
    WatermarkStrategy.no_watermarks(),
    "AOI Source"
)

spi_stream = env.from_source(
    spi_source,
    WatermarkStrategy.no_watermarks(),
    "SPI Source"
)

# =====================================================
# AOI PROCESSOR
# =====================================================

def process_aoi(record):

    try:

        data = json.loads(record)

        barcode = data.get("barcode")

        if not barcode:
            return record

        r = redis.Redis(
            host="redis",
            port=6379,
            decode_responses=True
        )

        added = r.sadd(
            "aoi_barcodes",
            barcode
        )

        update_metrics(r)

        print(
            f"AOI Processed | Barcode={barcode} | Added={added}"
        )

        return record

    except Exception as e:

        print(
            f"AOI ERROR : {str(e)}"
        )

        return record

# =====================================================
# SPI PROCESSOR
# =====================================================

def process_spi(record):

    try:

        data = json.loads(record)

        barcode = data.get("barcode")

        if not barcode:
            return record

        r = redis.Redis(
            host="redis",
            port=6379,
            decode_responses=True
        )

        added = r.sadd(
            "spi_barcodes",
            barcode
        )

        update_metrics(r)

        print(
            f"SPI Processed | Barcode={barcode} | Added={added}"
        )

        return record

    except Exception as e:

        print(
            f"SPI ERROR : {str(e)}"
        )

        return record

# =====================================================
# EXECUTION
# =====================================================

processed_aoi = aoi_stream.map(process_aoi)

processed_spi = spi_stream.map(process_spi)

# Required sinks

processed_aoi.print()

processed_spi.print()

print("Flink Reconciliation Started")

env.execute(
    "Manufacturing-Reconciliation"
)
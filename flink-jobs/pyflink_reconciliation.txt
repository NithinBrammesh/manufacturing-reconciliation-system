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
startup_redis.delete("fcr_barcodes")
startup_redis.delete("reconciliation_metrics")

print("Redis reconciliation data cleared")

# =====================================================
# METRICS CALCULATION
# =====================================================
def update_metrics(r):

    # =====================================================
    # FETCH REDIS SETS
    # =====================================================

    aoi_set = set(r.smembers("aoi_barcodes"))
    spi_set = set(r.smembers("spi_barcodes"))
    fcr_set = set(r.smembers("fcr_barcodes"))

    # =====================================================
    # TOTAL RECORDS
    # =====================================================

    total_aoi = len(aoi_set)
    total_spi = len(spi_set)
    total_fcr = len(fcr_set)

    # =====================================================
    # AOI ↔ SPI
    # =====================================================

    aoi_spi_matched = aoi_set.intersection(spi_set)
    aoi_missing_in_spi = aoi_set - spi_set
    spi_missing_in_aoi = spi_set - aoi_set

    # =====================================================
    # AOI ↔ FCR
    # =====================================================

    aoi_fcr_matched = aoi_set.intersection(fcr_set)
    aoi_missing_in_fcr = aoi_set - fcr_set
    fcr_missing_in_aoi = fcr_set - aoi_set

    # =====================================================
    # SPI ↔ FCR
    # =====================================================

    spi_fcr_matched = spi_set.intersection(fcr_set)
    spi_missing_in_fcr = spi_set - fcr_set
    fcr_missing_in_spi = fcr_set - spi_set


    # =====================================================
    # ALL THREE MACHINES
    # =====================================================

    all_matched = aoi_set.intersection(spi_set, fcr_set)

    all_match_count = len(all_matched)

    # =====================================================
    # OVERALL METRICS
    # =====================================================

    overall_total = len(aoi_set.union(spi_set, fcr_set))

    overall_percentage = (
        round((all_match_count / overall_total) * 100, 2)
        if overall_total else 0
    )

    # =====================================================
    # COUNTS
    # =====================================================

    aoi_spi_match_count = len(aoi_spi_matched)
    aoi_fcr_match_count = len(aoi_fcr_matched)
    spi_fcr_match_count = len(spi_fcr_matched)

    # =====================================================
    # STORE METRICS
    # =====================================================

    r.hset(
        "reconciliation_metrics",
        mapping={

            # -------------------------
            # Totals
            # -------------------------

            "total_aoi": total_aoi,
            "total_spi": total_spi,
            "total_fcr": total_fcr,

            "overall_total": overall_total,
            "overall_percentage": overall_percentage,

            # -------------------------
            # AOI ↔ SPI
            # -------------------------

            "aoi_spi_matched": aoi_spi_match_count,
            "aoi_missing_in_spi": len(aoi_missing_in_spi),
            "spi_missing_in_aoi": len(spi_missing_in_aoi),

            "aoi_spi_match_percentage":
                round((aoi_spi_match_count / total_aoi) * 100, 2)
                if total_aoi else 0,

            "aoi_spi_loss_percentage":
                round((len(aoi_missing_in_spi) / total_aoi) * 100, 2)
                if total_aoi else 0,

            "spi_aoi_match_percentage":
                round((aoi_spi_match_count / total_spi) * 100, 2)
                if total_spi else 0,

            "spi_aoi_loss_percentage":
                round((len(spi_missing_in_aoi) / total_spi) * 100, 2)
                if total_spi else 0,

            # -------------------------
            # AOI ↔ FCR
            # -------------------------

            "aoi_fcr_matched": aoi_fcr_match_count,
            "aoi_missing_in_fcr": len(aoi_missing_in_fcr),
            "fcr_missing_in_aoi": len(fcr_missing_in_aoi),

            "aoi_fcr_match_percentage":
                round((aoi_fcr_match_count / total_aoi) * 100, 2)
                if total_aoi else 0,

            "aoi_fcr_loss_percentage":
                round((len(aoi_missing_in_fcr) / total_aoi) * 100, 2)
                if total_aoi else 0,

            "fcr_aoi_match_percentage":
                round((aoi_fcr_match_count / total_fcr) * 100, 2)
                if total_fcr else 0,

            "fcr_aoi_loss_percentage":
                round((len(fcr_missing_in_aoi) / total_fcr) * 100, 2)
                if total_fcr else 0,

            # -------------------------
            # SPI ↔ FCR
            # -------------------------

            "spi_fcr_matched": spi_fcr_match_count,
            "all_matched": all_match_count,
            "spi_missing_in_fcr": len(spi_missing_in_fcr),
            "fcr_missing_in_spi": len(fcr_missing_in_spi),

            "spi_fcr_match_percentage":
                round((spi_fcr_match_count / total_spi) * 100, 2)
                if total_spi else 0,

            "spi_fcr_loss_percentage":
                round((len(spi_missing_in_fcr) / total_spi) * 100, 2)
                if total_spi else 0,

            "fcr_spi_match_percentage":
                round((spi_fcr_match_count / total_fcr) * 100, 2)
                if total_fcr else 0,

            "fcr_spi_loss_percentage":
                round((len(fcr_missing_in_spi) / total_fcr) * 100, 2)
                if total_fcr else 0
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
# FCR KAFKA SOURCE
# =====================================================

fcr_source = (
    KafkaSource.builder()
    .set_bootstrap_servers("kafka:9092")
    .set_topics("fcr-topic")
    .set_group_id("fcr-group")
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

fcr_stream = env.from_source(
    fcr_source,
    WatermarkStrategy.no_watermarks(),
    "FCR Source"
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

        # print(
        #     f"AOI Processed | Barcode={barcode} | Added={added}"
        # )

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

        # print(
        #     f"SPI Processed | Barcode={barcode} | Added={added}"
        # )

        return record

    except Exception as e:

        print(
            f"SPI ERROR : {str(e)}"
        )

        return record

# =====================================================
# FCR PROCESSOR
# =====================================================        

def process_fcr(record):

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

        r.sadd(
            "fcr_barcodes",
            barcode
        )

        update_metrics(r)

        return record

    except Exception as e:

        print(f"FCR ERROR : {str(e)}")

        return record

# =====================================================
# EXECUTION
# =====================================================

processed_aoi = aoi_stream.map(process_aoi)

processed_spi = spi_stream.map(process_spi)

processed_fcr = fcr_stream.map(process_fcr)

# Required sinks

processed_aoi.print()

processed_fcr.print()

processed_spi.print()

print("Flink Reconciliation Started")

env.execute(
    "Manufacturing-Reconciliation"
)
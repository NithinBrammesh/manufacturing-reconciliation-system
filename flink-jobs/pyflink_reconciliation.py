import json
import time
import redis

from update_metrics import update_metrics
from redis_events import (
    is_processing,
    start_processing,
    update_activity,
    publish_line_active
)

from load_config import topics, lines
from window_manager import get_current_window

print("Topics:", topics)
print("Lines:", lines)

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

# Register project modules for Beam Python worker
env.add_python_file("/opt/flink/jobs/update_metrics.py")
env.add_python_file("/opt/flink/jobs/load_config.py")
env.add_python_file("/opt/flink/jobs/redis_events.py")
env.add_python_file("/opt/flink/jobs/window_manager.py")
env.add_python_file("/opt/flink/jobs/config.env")

# =====================================================
# SAVE BARCODE
# =====================================================

def save_barcode(pipe, data, window_id):

    line        = data["line"]
    machine     = data["machine"]
    barcode     = data["barcode"]
    result      = data.get("result", "").upper()      # GOOD or BAD from PCBResult
    ts_ms       = data.get("timestamp_ms") or int(time.time() * 1000)
    source_type = data.get("sourceType", "").upper()  # SPI, FCR, AOI — from Node-RED

    if source_type == "SPI":

        # All SPI barcodes
        pipe.zadd(
            f"line:{line}:{machine}:{window_id}",
            {barcode: ts_ms}
        )

        # Split into GOOD and BAD
        if result == "GOOD":
            pipe.zadd(
                f"line:{line}:{machine}:GOOD:{window_id}",
                {barcode: ts_ms}
            )
        elif result == "BAD":
            pipe.zadd(
                f"line:{line}:{machine}:BAD:{window_id}",
                {barcode: ts_ms}
            )

    elif source_type == "FCR":

        # FCR just stores what it received — no split needed
        pipe.zadd(
            f"line:{line}:{machine}:{window_id}",
            {barcode: ts_ms}
        )

    else:

        # AOI or anything else
        pipe.zadd(
            f"line:{line}:{machine}:{window_id}",
            {barcode: ts_ms}
        )

# =====================================================
# UNIFIED PROCESSOR
# =====================================================

def process_record(record):

    r = redis.Redis(
        host="redis",
        port=6379,
        decode_responses=True
    )

    try:

        data = json.loads(record)

        barcode = data.get("barcode")

        if not barcode:
            return record

        line = data["line"]

        window_id = get_current_window(r, line)

        pipe = r.pipeline()

        # Store barcode
        save_barcode(pipe, data, window_id)

        # Processing state
        if not is_processing(r, line):

            print(f"[{line}] First message received")

            start_processing(pipe, line)

            publish_line_active(pipe, line)

        else:

            update_activity(pipe, line)

        # Execute pipeline
        pipe.execute()

        print("========== BEFORE update_metrics ==========")
        print(f"Processing Line: {line}, Window: {window_id}")

        update_metrics(r, line, window_id)

        print("========== AFTER update_metrics ==========")

        print(
            f"[{line}] "
            f"{data['machine']} "
            f"Barcode : {barcode} "
            f"Window : {window_id}"
        )

        return record

    except Exception as e:

        print("#############################")
        print("EXCEPTION OCCURRED")
        print(type(e))
        print(e)

        import traceback
        traceback.print_exc()

        print("#############################")

        return record

    finally:

        r.close()


# =====================================================
# STREAM PROCESSORS
# =====================================================

def process_aoi(record):
    return process_record(record)


def process_spi(record):
    return process_record(record)


def process_fcr(record):
    return process_record(record)


# =====================================================
# KAFKA SOURCES
# =====================================================

aoi_source = (
    KafkaSource.builder()
    .set_bootstrap_servers("kafka:9092")
    .set_topics(*topics["AOI"])
    .set_group_id("aoi-group")
    .set_starting_offsets(KafkaOffsetsInitializer.earliest())
    .set_value_only_deserializer(SimpleStringSchema())
    .build()
)

spi_source = (
    KafkaSource.builder()
    .set_bootstrap_servers("kafka:9092")
    .set_topics(*topics["SPI"])
    .set_group_id("spi-group")
    .set_starting_offsets(KafkaOffsetsInitializer.earliest())
    .set_value_only_deserializer(SimpleStringSchema())
    .build()
)

fcr_source = (
    KafkaSource.builder()
    .set_bootstrap_servers("kafka:9092")
    .set_topics(*topics["FCR"])
    .set_group_id("fcr-group")
    .set_starting_offsets(KafkaOffsetsInitializer.earliest())
    .set_value_only_deserializer(SimpleStringSchema())
    .build()
)

# =====================================================
# CREATE STREAMS
# =====================================================

aoi_stream = env.from_source(aoi_source, WatermarkStrategy.no_watermarks(), "AOI Source")
spi_stream = env.from_source(spi_source, WatermarkStrategy.no_watermarks(), "SPI Source")
fcr_stream = env.from_source(fcr_source, WatermarkStrategy.no_watermarks(), "FCR Source")

# =====================================================
# EXECUTION
# =====================================================

processed_aoi = aoi_stream.map(process_aoi)

processed_spi = spi_stream.map(process_spi)

processed_fcr = fcr_stream.map(process_fcr)


processed_aoi.print()
processed_spi.print()
processed_fcr.print()

if __name__ == "__main__":

    startup_redis = redis.Redis(
        host="redis",
        port=6379,
        decode_responses=True
    )

    # IMPORTANT: we do NOT wipe line:*, metrics:*, or window:* on
    # startup. Those now hold window-scoped history
    # (line:LINE1:AOI1:7, metrics:LINE1:7, window:LINE1, ...) that must
    # survive a Flink restart — otherwise restarting the job would
    # silently reset every line's active 24h window and lose history.
    # Only transient "is a line currently running" state gets cleared,
    # since that's meaningless to carry across a restart anyway.
    for key in startup_redis.scan_iter("processing:*"):
        startup_redis.delete(key)

    for key in startup_redis.scan_iter("status:*"):
        startup_redis.delete(key)

    startup_redis.close()

    print("Processing/status state cleared (barcode + window history preserved)")

    print("Flink Reconciliation Started")

    env.execute("Manufacturing-Reconciliation")
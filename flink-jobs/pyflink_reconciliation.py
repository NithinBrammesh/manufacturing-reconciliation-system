import json
import redis

from update_metrics import update_metrics
from redis_events import (
    is_processing,
    start_processing,
    update_activity,
    publish_line_active
)

from load_config import topics, lines

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
env.add_python_file("/opt/flink/jobs/config.env")  

# =====================================================
# SAVE BARCODE
# =====================================================

def save_barcode(pipe, data):

    line = data["line"]
    machine = data["machine"]
    barcode = data["barcode"]

    pipe.sadd(
        f"line:{line}:{machine}",
        barcode
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

        pipe = r.pipeline()

        # Store barcode
        save_barcode(pipe, data)

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
        print(f"Processing Line: {line}")

        update_metrics(r, line)

        print("========== AFTER update_metrics ==========")

        print(
            f"[{line}] "
            f"{data['machine']} "
            f"Barcode : {barcode}"
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

    for key in startup_redis.scan_iter("metrics:*"):
        startup_redis.delete(key)

    for key in startup_redis.scan_iter("line:*"):
        startup_redis.delete(key)

    for key in startup_redis.scan_iter("processing:*"):
        startup_redis.delete(key)

    startup_redis.close()

    print("Redis reconciliation data cleared")

    print("Flink Reconciliation Started")

    env.execute("Manufacturing-Reconciliation")
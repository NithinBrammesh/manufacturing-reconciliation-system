import json
import time
import redis

# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

LINE_EVENTS_CHANNEL = "line_events"


# ------------------------------------------------------------------
# Processing Key
# ------------------------------------------------------------------

def processing_key(line: str) -> str:
    """Return Redis processing key for a production line."""
    return f"processing:{line}"


# ------------------------------------------------------------------
# Processing State
# ------------------------------------------------------------------

def is_processing(r: redis.Redis, line: str) -> bool:
    """
    Check whether the line is currently processing.
    """
    return r.exists(processing_key(line)) == 1


def start_processing(pipe: redis.client.Pipeline, line: str):
    """
    Create processing hash.

    NOTE:
    This should be called ONLY inside a Redis pipeline.
    """

    now = int(time.time())

    pipe.hset(
        processing_key(line),
        mapping={
            "state": "ACTIVE",
            "started_at": now,
            "last_activity": now,
            "message_count": 1,
        },
    )


def update_activity(pipe: redis.client.Pipeline, line: str):
    """
    Update activity for every incoming barcode.

    NOTE:
    This should be called ONLY inside a Redis pipeline.
    """

    now = int(time.time())

    key = processing_key(line)

    pipe.hset(
        key,
        mapping={
            "last_activity": now
        }
    )

    pipe.hincrby(
        key,
        "message_count",
        1
    )


def get_processing(r: redis.Redis, line: str) -> dict:
    """
    Return processing hash as decoded dictionary.
    """

    data = r.hgetall(processing_key(line))

    return {
        k.decode(): v.decode()
        for k, v in data.items()
    }


def clear_processing(pipe: redis.client.Pipeline, line: str):
    """
    Remove processing state.

    NOTE:
    Should be executed from a pipeline.
    """

    pipe.delete(processing_key(line))


# ------------------------------------------------------------------
# Pub/Sub
# ------------------------------------------------------------------

def publish_line_active(pipe: redis.client.Pipeline, line: str):
    """
    Publish LINE_ACTIVE event.

    NOTE:
    Publish is intentionally inside the pipeline so that:
    - barcode storage
    - processing hash
    - publish

    happen in one Redis round-trip.
    """

    payload = json.dumps({
        "event": "LINE_ACTIVE",
        "line": line,
        "timestamp": int(time.time())
    })

    pipe.publish(
        LINE_EVENTS_CHANNEL,
        payload
    )


def subscribe(r: redis.Redis):
    """
    Subscribe to Redis Pub/Sub channel.

    Used by aggregation_service.py
    """

    pubsub = r.pubsub()

    pubsub.subscribe(LINE_EVENTS_CHANNEL)

    return pubsub


# ------------------------------------------------------------------
# Helper
# ------------------------------------------------------------------

def decode_message(message):
    """
    Decode Pub/Sub message.

    Returns None for subscription messages.
    """

    if message["type"] != "message":
        return None

    return json.loads(message["data"])


# ------------------------------------------------------------------
# Debug
# ------------------------------------------------------------------

if __name__ == "__main__":

    r = redis.Redis(
        host="localhost",
        port=6379,
        decode_responses=False
    )

    print("Publishing test event...")

    pipe = r.pipeline()

    publish_line_active(pipe, "LINE1")

    pipe.execute()

    print("Done.")
import json
import redis
from redis_events import subscribe, decode_message

print("Aggregation service started...")

r = redis.Redis(
    host="redis",
    port=6379,
    decode_responses=True
)

pubsub = subscribe(r)

print("Listening for line events...\n")

for message in pubsub.listen():

    event = decode_message(message)

    if event is None:
        continue

    line       = event.get("line")
    event_type = event.get("event")
    timestamp  = event.get("timestamp")

    print(f"[{event_type}] Line: {line}")

    if event_type == "LINE_ACTIVE":

        r.hset(f"status:{line}", mapping={
            "state": "ACTIVE",
            "since": timestamp
        })

    elif event_type == "LINE_IDLE":

        r.hset(f"status:{line}", mapping={
            "state": "IDLE",
            "since": timestamp
        })
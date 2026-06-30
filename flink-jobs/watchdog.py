import json
import time
import redis

IDLE_TIMEOUT = 30
POLL_INTERVAL = 5

print("Watchdog started. Monitoring for idle lines...")

while True:

    try:

        r = redis.Redis(
            host="redis",
            port=6379,
            decode_responses=True
        )

        now = int(time.time())

        for key in r.scan_iter("processing:*"):

            line = key.split(":")[1]

            data = r.hgetall(key)

            last_activity = data.get("last_activity")
            state         = data.get("state")

            if not last_activity:
                continue

            idle_for = now - int(last_activity)

            print(f"[{line}] state={state} idle_for={idle_for}s")

            if idle_for >= IDLE_TIMEOUT:

                print(f"[{line}] IDLE — no activity for {idle_for}s. Publishing LINE_IDLE.")

                # Publish LINE_IDLE event
                r.publish("line_events", json.dumps({
                    "event":     "LINE_IDLE",
                    "line":      line,
                    "timestamp": now
                }))

                # Update state to IDLE (don't delete — dashboard needs to read it)
                r.hset(key, mapping={
                    "state":         "IDLE",
                    "last_activity": last_activity
                })

                # Also write to status key for Flask API
                r.hset(f"status:{line}", mapping={
                    "state": "IDLE",
                    "since": now
                })

            else:

                # Line is active — keep status key updated
                r.hset(f"status:{line}", mapping={
                    "state": "ACTIVE",
                    "since": data.get("started_at", now)
                })

        r.close()

    except Exception as e:
        print(f"Watchdog error: {e}")

    time.sleep(POLL_INTERVAL)
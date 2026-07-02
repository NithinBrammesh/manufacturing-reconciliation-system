import json
import time
import redis

IDLE_TIMEOUT = 30
POLL_INTERVAL = 5

print("Watchdog started. Monitoring for idle lines...")

# Single long-lived connection instead of reconnecting every 5s
r = redis.Redis(
    host="redis",
    port=6379,
    decode_responses=True
)

while True:

    try:

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

                # Only fire IDLE transition once, not every poll
                if state != "IDLE":

                    print(f"[{line}] IDLE — no activity for {idle_for}s. Publishing LINE_IDLE.")

                    r.publish("line_events", json.dumps({
                        "event":     "LINE_IDLE",
                        "line":      line,
                        "timestamp": now
                    }))

                    r.hset(key, mapping={
                        "state": "IDLE",
                    })

                    r.hset(f"status:{line}", mapping={
                        "state": "IDLE",
                        "since": now
                    })

            else:

                if state == "IDLE":

                    # Line just came back to life — pyflink's is_processing()
                    # still sees this hash as existing, so it never calls
                    # start_processing()/publish_line_active() again on its own.
                    # Watchdog treats "fresh activity + stale IDLE state" as
                    # a reactivation and restarts the session itself.

                    print(f"[{line}] REACTIVATED — no longer idle. Publishing LINE_ACTIVE.")

                    r.hset(key, mapping={
                        "state":      "ACTIVE",
                        "started_at": now,
                    })

                    r.publish("line_events", json.dumps({
                        "event":     "LINE_ACTIVE",
                        "line":      line,
                        "timestamp": now
                    }))

                    r.hset(f"status:{line}", mapping={
                        "state": "ACTIVE",
                        "since": now
                    })

                else:

                    # Already active — keep status key in sync
                    r.hset(f"status:{line}", mapping={
                        "state": "ACTIVE",
                        "since": data.get("started_at", now)
                    })

    except Exception as e:
        print(f"Watchdog error: {e}")

    time.sleep(POLL_INTERVAL)
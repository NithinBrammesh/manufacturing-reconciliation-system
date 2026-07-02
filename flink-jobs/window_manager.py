import time
import redis
from load_config import lines

# ==========================================================
# Configuration
# ==========================================================

WINDOW_DURATION_MS = 24 * 60 * 60 * 1000  # 24 Hours


# ==========================================================
# Redis Key
# ==========================================================

def window_key(line: str) -> str:
    """
    Redis key storing the active window metadata
    for a production line.
    """
    return f"window:{line}"


# ==========================================================
# Create New Window
# ==========================================================

def create_new_window(r: redis.Redis, line: str) -> int:
    """
    Creates a new 24-hour window.

    Returns:
        window_id
    """

    now = int(time.time() * 1000)

    key = window_key(line)

    previous = r.hget(key, "window_id")

    if previous is None:

        window_id = 1

    else:

        previous_window = int(previous)

        # Clear previous completed window
        delete_window_data(
            r,
            line,
            previous_window
        )

        window_id = previous_window + 1


    r.hset(
        key,
        mapping={
            "window_id": window_id,
            "start_ms": now,
            "end_ms": now + WINDOW_DURATION_MS
        }
    )

    print(f"[{line}] Created Window #{window_id}")

    return window_id


# ==========================================================
# Check Expiry
# ==========================================================

def is_window_expired(window: dict) -> bool:
    """
    Checks whether the active window has completed 24 hours.
    """

    if not window:
        return True

    end_ms = int(window["end_ms"])
    now = int(time.time() * 1000)

    return now >= end_ms


# ==========================================================
# Get Current Window
# ==========================================================

def get_current_window(r: redis.Redis, line: str) -> int:
    """
    Returns the active window id.

    Creates a new window when:
    - first barcode arrives, OR
    - previous window expired.

    NOTE: call this ONCE per incoming record, in process_record(),
    and reuse the returned window_id for both save_barcode() and
    update_metrics(). Don't call this a second time within the same
    record's processing — see pyflink_reconciliation.py.
    """

    key = window_key(line)

    window = r.hgetall(key)

    if not window:
        return create_new_window(r, line)

    if is_window_expired(window):
        return create_new_window(r, line)

    return int(window["window_id"])


# ==========================================================
# Get Window Metadata
# ==========================================================

def get_window_info(r: redis.Redis, line: str):
    return r.hgetall(window_key(line))



# ==========================================================
# Delete Previous Window
# ==========================================================

def delete_window_data(
    r: redis.Redis,
    line: str,
    window_id: int
):
    """
    Deletes all Redis data belonging to one completed
    production window.
    """

    print(f"[{line}] Clearing completed Window #{window_id}")

    pipe = r.pipeline()

    line_config = lines.get(line)

    if line_config:

        for machine in line_config:

            machine_name = machine["machine"]

            pipe.delete(
                f"line:{line}:{machine_name}:{window_id}"
            )

    pipe.delete(
        f"metrics:{line}:{window_id}"
    )

    pipe.execute()

    print(f"[{line}] Window #{window_id} deleted")

# ==========================================================
# Debug
# ==========================================================

if __name__ == "__main__":

    r = redis.Redis(
        host="localhost",
        port=6379,
        decode_responses=True
    )

    while True:
        window = get_current_window(r, "LINE1")
        print(window)
        print(get_window_info(r, "LINE1"))
        time.sleep(5)
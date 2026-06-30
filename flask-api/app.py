from flask import Flask, jsonify
from flask_cors import CORS
import redis
import os
import time
import json
from flask import Response, stream_with_context

app = Flask(__name__)
CORS(app)

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

@app.route("/api/reconciliation", methods=["GET"])
def get_reconciliation():
    metric_keys = sorted(r.keys("metrics:*"))
    response = {}
    for key in metric_keys:
        line = key.split(":")[1]
        response[line] = r.hgetall(key)
    return jsonify(response)

@app.route("/api/lines", methods=["GET"])
def get_lines():
    metric_keys = sorted(r.keys("metrics:*"))
    lines = [key.split(":")[1] for key in metric_keys]
    return jsonify(lines)

@app.route("/api/reconciliation/<line>", methods=["GET"])
def get_line_metrics(line):
    metrics = r.hgetall(f"metrics:{line}")
    if not metrics:
        return jsonify({"error": "Line not found"}), 404
    return jsonify(metrics)

@app.route("/api/summary", methods=["GET"])
def get_summary():
    """Quick overview of all lines — useful for dashboard header cards."""
    metric_keys = sorted(r.keys("metrics:*"))
    summary = []
    for key in metric_keys:
        line = key.split(":")[1]
        m = r.hgetall(key)
        summary.append({
            "line": line,
            "total_aoi": m.get("total_aoi", 0),
            "total_spi": m.get("total_spi", 0),
            "total_fcr": m.get("total_fcr", 0),
            "all_matched": m.get("all_matched", 0),
            "overall_percentage": m.get("overall_percentage", 0),
        })
    return jsonify(summary)

@app.route("/health", methods=["GET"])
def health():
    try:
        r.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "disconnected"
    return jsonify({
        "status": "running",
        "redis": redis_status,
        "service": "Manufacturing Reconciliation API",
        "version": "2.0"
    })

@app.route("/api/status", methods=["GET"])
def get_status():
    status_keys = sorted(r.keys("status:*"))

    response = {}

    for key in status_keys:
        line = key.split(":")[1]
        data = r.hgetall(key)

        response[line] = {
            "state": data.get("state", "UNKNOWN"),
            "since": int(data.get("since", 0))
        }

    return jsonify(response)



@app.route("/events")
def sse_events():
    """
    SSE endpoint — streams metrics + status to the browser.
    Browser connects once and receives updates automatically.
    """
    def stream():
        pubsub = r.pubsub()
        pubsub.subscribe("line_events")

        try:
            # Send current snapshot immediately on connect
            snapshot = build_snapshot()
            yield f"data: {json.dumps(snapshot)}\n\n"

            # Then stream updates as Redis Pub/Sub events arrive
            for message in pubsub.listen():

                if message["type"] != "message":
                    continue

                # On any event, send fresh snapshot to all connected clients
                snapshot = build_snapshot()
                yield f"data: {json.dumps(snapshot)}\n\n"

        except GeneratorExit:
            pubsub.unsubscribe()

    return Response(
        stream_with_context(stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        }
    )


def build_snapshot():
    """Build a complete snapshot of metrics + status for all lines."""
    metric_keys = sorted(r.keys("metrics:*"))
    metrics = {}
    for key in metric_keys:
        line = key.split(":")[1]
        metrics[line] = r.hgetall(key)

    status_keys = sorted(r.keys("status:*"))
    status = {}
    for key in status_keys:
        line = key.split(":")[1]
        data = r.hgetall(key)
        status[line] = {
            "state": data.get("state", "UNKNOWN"),
            "since": int(data.get("since", 0))
        }

    return {"metrics": metrics, "status": status}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
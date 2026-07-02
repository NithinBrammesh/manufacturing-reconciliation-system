import json
import time
import redis
from itertools import combinations
from load_config import lines


def update_metrics(r: redis.Redis, line_name: str, window_id: int):
    """
    Calculates and stores reconciliation metrics for a single
    production window.

    update_metrics() never decides which window is active — it only
    ever operates on the window_id it's given by process_record()
    (via window_manager.get_current_window()).
    """

    line_config = lines.get(line_name)

    if not line_config:
        return

    machine_data = {}

    # --------------------------------------------------------
    # Read barcode ZSETs for all configured machines, scoped to
    # this specific production window
    # --------------------------------------------------------

    pipe = r.pipeline()
    redis_keys = []

    for machine in line_config:
        machine_name = machine["machine"]
        redis_key = f"line:{line_name}:{machine_name}:{window_id}"
        redis_keys.append((machine_name, machine["type"]))
        # ZRANGE instead of SMEMBERS — barcodes are stored in a ZSET
        # (member=barcode, score=arrival timestamp in ms). We only need
        # the members here; the timestamp is available via ZSCORE later
        # if you ever need per-barcode arrival time.
        pipe.zrange(redis_key, 0, -1)

    results = pipe.execute()

    # Build type_sets dynamically
    type_sets = {}

    for (machine_name, machine_type), barcodes in zip(redis_keys, results):
        machine_data[machine_name] = set(barcodes)
        if machine_type not in type_sets:
            type_sets[machine_type] = set()
        type_sets[machine_type].update(machine_data[machine_name])

    # --------------------------------------------------------
    # Global union — every unique barcode seen by ANY machine
    # --------------------------------------------------------

    all_barcodes = set()
    for s in type_sets.values():
        all_barcodes.update(s)

    total_unique = len(all_barcodes)

    # --------------------------------------------------------
    # Overall metrics (barcodes seen by ALL machines)
    # --------------------------------------------------------

    available_sets = [s for s in type_sets.values() if s]

    if len(available_sets) >= 2:
        matched = available_sets[0].copy()
        for s in available_sets[1:]:
            matched &= s
        all_match_count = len(matched)
        overall_total = len(set.union(*available_sets))
    elif len(available_sets) == 1:
        all_match_count = 0
        overall_total = len(available_sets[0])
    else:
        all_match_count = 0
        overall_total = 0

    overall_percentage = (
        round((all_match_count / overall_total) * 100, 2)
        if overall_total else 0
    )

    # --------------------------------------------------------
    # Build mapping
    # --------------------------------------------------------

    mapping = {}

    mapping["window_id"] = window_id
    mapping["last_updated_ms"] = int(time.time() * 1000)

    # Per-type totals and has_ flags
    for machine_type, barcodes in type_sets.items():
        key = machine_type.lower()
        mapping[f"total_{key}"] = len(barcodes)
        mapping[f"has_{key}"]   = int(bool(barcodes))

    # Overall
    mapping["overall_total"]         = overall_total
    mapping["overall_percentage"]    = overall_percentage
    mapping["all_matched"]           = all_match_count
    mapping["total_unique_barcodes"] = total_unique

    # --------------------------------------------------------
    # Global loss per machine
    # (how many of ALL unique barcodes did this machine miss?)
    # --------------------------------------------------------

    global_unique_map = {}

    for machine_type, barcodes in type_sets.items():
        key = machine_type.lower()

        missing_globally = all_barcodes - barcodes
        present_globally = all_barcodes & barcodes

        others_union = set()
        for other_type, other_set in type_sets.items():
            if other_type != machine_type:
                others_union.update(other_set)
        exclusive_to_machine = barcodes - others_union

        mapping[f"{key}_global_seen"]        = len(barcodes)
        mapping[f"{key}_global_missing"]     = len(missing_globally)
        mapping[f"{key}_global_match_pct"]   = round(len(present_globally) / total_unique * 100, 2) if total_unique else 0
        mapping[f"{key}_global_loss_pct"]    = round(len(missing_globally) / total_unique * 100, 2) if total_unique else 0
        mapping[f"{key}_exclusive_barcodes"] = len(exclusive_to_machine)
        mapping[f"{key}_missing_barcodes"]   = json.dumps(sorted(list(missing_globally)))

        global_unique_map[machine_type] = sorted(list(exclusive_to_machine))

        print(f"[{line_name}] window={window_id} {machine_type} — seen: {len(barcodes)}, "
              f"missing globally: {len(missing_globally)}, "
              f"exclusive: {len(exclusive_to_machine)}")

    mapping["global_unique_barcodes"] = json.dumps(global_unique_map)

    # --------------------------------------------------------
    # Pairwise comparisons — fully dynamic
    # --------------------------------------------------------

    comparison_list = []

    for source_type, target_type in combinations(type_sets.keys(), 2):

        source_set = type_sets[source_type]
        target_set = type_sets[target_type]

        s = source_type.lower()
        t = target_type.lower()

        matched_set    = source_set & target_set
        source_missing = source_set - target_set
        target_missing = target_set - source_set

        total_source = len(source_set)
        total_target = len(target_set)

        mapping[f"{s}_{t}_matched"]          = len(matched_set)
        mapping[f"{s}_missing_in_{t}"]       = len(source_missing)
        mapping[f"{t}_missing_in_{s}"]       = len(target_missing)

        mapping[f"{s}_{t}_match_percentage"] = round(len(matched_set) / total_source * 100, 2) if total_source else 0
        mapping[f"{s}_{t}_loss_percentage"]  = round(len(source_missing) / total_source * 100, 2) if total_source else 0
        mapping[f"{t}_{s}_match_percentage"] = round(len(matched_set) / total_target * 100, 2) if total_target else 0
        mapping[f"{t}_{s}_loss_percentage"]  = round(len(target_missing) / total_target * 100, 2) if total_target else 0

        comparison_list.append(f"{source_type}_{target_type}")

    mapping["comparisons"] = json.dumps(comparison_list)

    # --------------------------------------------------------
    # Write to Redis
    #
    # 1. metrics:{line}:{window_id} — permanent snapshot for this
    #    specific 24h production window (history).
    # 2. metrics:{line}             — "live" pointer, always mirrors
    #    the current window's data, so existing Flask endpoints
    #    (/api/reconciliation, /events, etc.) keep working unchanged.
    # --------------------------------------------------------

    r.hset(f"metrics:{line_name}:{window_id}", mapping=mapping)
    r.hset(f"metrics:{line_name}", mapping=mapping)

    print(
        f"[{line_name}] Metrics updated "
        f"(window_id={window_id}) — "
        f"pairs: {comparison_list}, total unique: {total_unique}"
    )
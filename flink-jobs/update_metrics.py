import json
import time
import redis
from itertools import combinations
from load_config import lines


def update_rework_metrics(r, line_name, window_id, type_sets, mapping):
    """
    Reconciles SPI Bad barcodes against FCR received barcodes.
    Called from update_metrics() before writing to Redis.
    """

    line_config = lines.get(line_name)
    if not line_config:
        return

    all_spi_bad  = set()
    all_spi_good = set()
    spi_split_by_machine = {}

    for machine in line_config:
        machine_name = machine["machine"]
        machine_type = machine["type"]

        if machine_type != "SPI":
            continue

        bad_key  = f"line:{line_name}:{machine_name}:BAD:{window_id}"
        good_key = f"line:{line_name}:{machine_name}:GOOD:{window_id}"

        bad_barcodes  = set(r.zrange(bad_key,  0, -1))
        good_barcodes = set(r.zrange(good_key, 0, -1))

        all_spi_bad.update(bad_barcodes)
        all_spi_good.update(good_barcodes)

        total = len(good_barcodes) + len(bad_barcodes)

        spi_split_by_machine[machine_name] = {
            "good":       sorted(list(good_barcodes)),
            "bad":        sorted(list(bad_barcodes)),
            "good_count": len(good_barcodes),
            "bad_count":  len(bad_barcodes),
            "total":      total,
            "good_pct":   round(len(good_barcodes) / total * 100, 2) if total else 0,
            "bad_pct":    round(len(bad_barcodes)  / total * 100, 2) if total else 0,
        }

    # No SPI Good/Bad data yet — result field not in messages
    if not all_spi_bad and not all_spi_good:
        return

    fcr_set   = type_sets.get("FCR", set())
    total_spi = len(all_spi_good) + len(all_spi_bad)

    # SPI Good/Bad split totals
    mapping["spi_total_barcodes"] = total_spi
    mapping["spi_good_count"]     = len(all_spi_good)
    mapping["spi_bad_count"]      = len(all_spi_bad)
    mapping["spi_good_pct"]       = round(len(all_spi_good) / total_spi * 100, 2) if total_spi else 0
    mapping["spi_bad_pct"]        = round(len(all_spi_bad)  / total_spi * 100, 2) if total_spi else 0
    mapping["spi_good_barcodes"]  = json.dumps(sorted(list(all_spi_good)))
    mapping["spi_bad_barcodes"]   = json.dumps(sorted(list(all_spi_bad)))
    mapping["spi_split_by_machine"] = json.dumps(spi_split_by_machine)

    # FCR rework reconciliation
    if all_spi_bad:
        fcr_received_bad = fcr_set & all_spi_bad
        fcr_missing_bad  = all_spi_bad - fcr_set
        fcr_unexpected   = fcr_set - all_spi_bad

        mapping["fcr_expected"]            = len(all_spi_bad)
        mapping["fcr_received_bad"]        = len(fcr_received_bad)
        mapping["fcr_missing_bad"]         = len(fcr_missing_bad)
        mapping["fcr_unexpected"]          = len(fcr_unexpected)

        mapping["fcr_rework_coverage_pct"] = round(
            len(fcr_received_bad) / len(all_spi_bad) * 100, 2
        ) if all_spi_bad else 0

        mapping["fcr_rework_loss_pct"]     = round(
            len(fcr_missing_bad) / len(all_spi_bad) * 100, 2
        ) if all_spi_bad else 0

        mapping["fcr_missing_bad_barcodes"] = json.dumps(
            sorted(list(fcr_missing_bad))
        )
        mapping["fcr_unexpected_barcodes"]  = json.dumps(
            sorted(list(fcr_unexpected))
        )

        print(f"[{line_name}] SPI Bad: {len(all_spi_bad)}, "
              f"FCR received: {len(fcr_received_bad)}, "
              f"Rework loss: {len(fcr_missing_bad)}")


def update_metrics(r: redis.Redis, line_name: str, window_id: int):

    line_config = lines.get(line_name)
    if not line_config:
        return

    machine_data = {}
    pipe = r.pipeline()
    redis_keys = []

    for machine in line_config:
        machine_name = machine["machine"]
        redis_key = f"line:{line_name}:{machine_name}:{window_id}"
        redis_keys.append((machine_name, machine["type"]))
        pipe.zrange(redis_key, 0, -1)

    results = pipe.execute()

    type_sets = {}
    for (machine_name, machine_type), barcodes in zip(redis_keys, results):
        machine_data[machine_name] = set(barcodes)
        if machine_type not in type_sets:
            type_sets[machine_type] = set()
        type_sets[machine_type].update(machine_data[machine_name])

    all_barcodes = set()
    for s in type_sets.values():
        all_barcodes.update(s)
    total_unique = len(all_barcodes)

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

    mapping = {}
    mapping["window_id"]      = window_id
    mapping["last_updated_ms"] = int(time.time() * 1000)

    for machine_type, barcodes in type_sets.items():
        key = machine_type.lower()
        mapping[f"total_{key}"] = len(barcodes)
        mapping[f"has_{key}"]   = int(bool(barcodes))

    mapping["overall_total"]         = overall_total
    mapping["overall_percentage"]    = overall_percentage
    mapping["all_matched"]           = all_match_count
    mapping["total_unique_barcodes"] = total_unique

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
        global_unique_map[machine_type]      = sorted(list(exclusive_to_machine))

    mapping["global_unique_barcodes"] = json.dumps(global_unique_map)

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

    # ── Rework metrics ──────────────────────────────────────────
    update_rework_metrics(r, line_name, window_id, type_sets, mapping)

    # ── Write to Redis ──────────────────────────────────────────
    r.hset(f"metrics:{line_name}:{window_id}", mapping=mapping)
    r.hset(f"metrics:{line_name}", mapping=mapping)

    print(f"[{line_name}] Metrics updated (window_id={window_id}) — "
          f"pairs: {comparison_list}, total unique: {total_unique}")
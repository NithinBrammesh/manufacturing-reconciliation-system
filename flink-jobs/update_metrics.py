import json
import redis
from itertools import combinations
from load_config import lines


def update_metrics(r: redis.Redis, line_name: str):

    line_config = lines.get(line_name)

    if not line_config:
        return

    machine_data = {}

    # --------------------------------------------------------
    # Read barcode sets for all configured machines
    # --------------------------------------------------------

    pipe = r.pipeline()
    redis_keys = []

    for machine in line_config:
        machine_name = machine["machine"]
        redis_key = f"line:{line_name}:{machine_name}"
        redis_keys.append((machine_name, machine["type"]))
        pipe.smembers(redis_key)

    results = pipe.execute()

    # Build type_sets dynamically — works for ANY machine types
    type_sets = {}

    for (machine_name, machine_type), barcodes in zip(redis_keys, results):
        machine_data[machine_name] = set(barcodes)
        if machine_type not in type_sets:
            type_sets[machine_type] = set()
        type_sets[machine_type].update(machine_data[machine_name])

    # --------------------------------------------------------
    # Overall metrics
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
    # Build mapping dynamically
    # --------------------------------------------------------

    mapping = {}

    # Per-type totals and has_ flags — dynamic
    for machine_type, barcodes in type_sets.items():
        key = machine_type.lower()
        mapping[f"total_{key}"] = len(barcodes)
        mapping[f"has_{key}"] = int(bool(barcodes))

    # Overall
    mapping["overall_total"]      = overall_total
    mapping["overall_percentage"] = overall_percentage
    mapping["all_matched"]        = all_match_count

    # --------------------------------------------------------
    # Pairwise comparisons — fully dynamic using combinations
    # --------------------------------------------------------

    comparison_list = []

    for source_type, target_type in combinations(type_sets.keys(), 2):

        source_set = type_sets[source_type]
        target_set = type_sets[target_type]

        s = source_type.lower()
        t = target_type.lower()

        matched_set      = source_set & target_set
        source_missing   = source_set - target_set
        target_missing   = target_set - source_set

        total_source = len(source_set)
        total_target = len(target_set)

        mapping[f"{s}_{t}_matched"]           = len(matched_set)
        mapping[f"{s}_missing_in_{t}"]        = len(source_missing)
        mapping[f"{t}_missing_in_{s}"]        = len(target_missing)

        mapping[f"{s}_{t}_match_percentage"]  = round(len(matched_set) / total_source * 100, 2) if total_source else 0
        mapping[f"{s}_{t}_loss_percentage"]   = round(len(source_missing) / total_source * 100, 2) if total_source else 0
        mapping[f"{t}_{s}_match_percentage"]  = round(len(matched_set) / total_target * 100, 2) if total_target else 0
        mapping[f"{t}_{s}_loss_percentage"]   = round(len(target_missing) / total_target * 100, 2) if total_target else 0

        # Store comparison pair names so frontend knows what pairs exist
        comparison_list.append(f"{source_type}_{target_type}")

    # Tell the frontend exactly which pairs exist for this line
    mapping["comparisons"] = json.dumps(comparison_list)

    # --------------------------------------------------------
    # Write to Redis
    # --------------------------------------------------------

    r.hset(f"metrics:{line_name}", mapping=mapping)

    print(f"[{line_name}] Metrics updated — pairs: {comparison_list}")
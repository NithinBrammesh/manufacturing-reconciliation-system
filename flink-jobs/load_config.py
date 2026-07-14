from pathlib import Path
from dotenv import dotenv_values

# =========================================
# Locate config.env — works in both
# the JobManager and the Beam worker
# =========================================

_this_dir = Path(__file__).parent
_fallback  = Path("/opt/flink/jobs")

_candidates = [
    _this_dir / "config.env",
    _fallback  / "config.env",
]

_env_path = next((p for p in _candidates if p.exists()), None)

if _env_path is None:
    raise FileNotFoundError(
        f"config.env not found in {_this_dir} or {_fallback}"
    )

config = dotenv_values(_env_path)

print(type(config))

# =========================================
# Parse Config
# =========================================

line_config = {}

for key, value in config.items():
    if value:
        line_config[key] = value.split(",")

# =========================================
# Kafka Topics Dictonaries
# =========================================

topics = {
    "AOI": line_config.get("AOI_TOPICS", []),
    "SPI": line_config.get("SPI_TOPICS", []),
    "FCR": line_config.get("FCR_TOPICS", [])
}

# =========================================
# Manufacturing Lines
# =========================================

lines = {}

for key, value in line_config.items():

    if key.startswith("LINE"):

        lines[key] = []             # Empty list for productionline

        for machine in value:

            machine_type, machine_name = machine.split("|")

            lines[key].append({
                "type": machine_type,
                "machine": machine_name
            })

# =========================================
# Test
# =========================================

if __name__ == "__main__":

    print("Topics:")
    print(topics)

    print("\nLines:")
    print(lines)
from pathlib import Path
from dotenv import dotenv_values

# ==========================
# Load config.env
# ==========================

BASE_DIR = Path(__file__).parent

config = dotenv_values(BASE_DIR / "config.env")

# ==========================
# Parse Config
# ==========================

line_config = {}

for key, value in config.items():
    if value:
        line_config[key] = value.split(",")

# ==========================
# Kafka Topics
# ==========================

topics = {
    "AOI": line_config.get("AOI_TOPICS", []),
    "SPI": line_config.get("SPI_TOPICS", []),
    "FCR": line_config.get("FCR_TOPICS", [])
}

# ==========================
# Manufacturing Lines
# ==========================

lines = {}

for key, value in line_config.items():

    if key.startswith("LINE"):

        lines[key] = []

        for machine in value:

            machine_type, machine_name = machine.split("|")

            lines[key].append({
                "type": machine_type,
                "machine": machine_name
            })

# ==========================
# Test
# ==========================

if __name__ == "__main__":

    print("Topics:")
    print(topics)

    print("\nLines:")
    print(lines)
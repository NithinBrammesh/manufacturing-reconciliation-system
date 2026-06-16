import json

# ============================
# Read SPI Records
# ============================

with open("reports/spi_records_from_kafka.json", "r") as f:
    spi_data = json.load(f)

spi_barcodes = set()

for record in spi_data:
    spi_barcodes.add(record["barcode"])

# ============================
# Read AOI Records
# ============================

with open("reports/aoi_records_from_kafka.json", "r") as f:
    aoi_data = json.load(f)

aoi_barcodes = set()

for record in aoi_data:
    aoi_barcodes.add(record["barcode"])

# ============================
# Counts
# ============================

spi_count = len(spi_barcodes)
aoi_count = len(aoi_barcodes)

missing_in_aoi = spi_barcodes - aoi_barcodes
extra_in_aoi = aoi_barcodes - spi_barcodes
matched_barcodes = spi_barcodes & aoi_barcodes

missing_in_aoi_count = len(missing_in_aoi)
extra_in_aoi_count = len(extra_in_aoi)
matched_count = len(matched_barcodes)

# ============================
# Percentages
# ============================

spi_to_aoi_loss_pct = 0

if spi_count > 0:
    spi_to_aoi_loss_pct = (
        missing_in_aoi_count / spi_count
    ) * 100

aoi_extra_pct = 0

if aoi_count > 0:
    aoi_extra_pct = (
        extra_in_aoi_count / aoi_count
    ) * 100

# ============================
# JSON Report
# ============================

report = {
    "spi_count": spi_count,
    "aoi_count": aoi_count,
    "matched_count": matched_count,
    "missing_in_aoi": missing_in_aoi_count,
    "extra_in_aoi": extra_in_aoi_count,
    "loss_percentage": round(spi_to_aoi_loss_pct, 2),
    "extra_percentage": round(aoi_extra_pct, 2)
}

with open("reports/reconciliation_report.json", "w") as f:
    json.dump(report, f, indent=4)

# ============================
# Text Report
# ============================

with open("reports/reconciliation_report.txt", "w") as f:

    f.write("KAFKA RECONCILIATION REPORT\n")
    f.write("===========================\n\n")

    f.write(f"SPI Count      : {spi_count}\n")
    f.write(f"AOI Count      : {aoi_count}\n")
    f.write(f"Matched Count  : {matched_count}\n\n")

    f.write(f"Missing In AOI : {missing_in_aoi_count}\n")
    f.write(f"Loss Percentage: {spi_to_aoi_loss_pct:.2f}%\n\n")

    f.write(f"Extra In AOI   : {extra_in_aoi_count}\n")
    f.write(f"Extra Percentage: {aoi_extra_pct:.2f}%\n")

# ============================
# Console Output
# ============================

print("\n===================================")
print("KAFKA RECONCILIATION REPORT")
print("===================================")

print(f"\nSPI Count      : {spi_count}")
print(f"AOI Count      : {aoi_count}")
print(f"Matched Count  : {matched_count}")

print(f"\nMissing In AOI : {missing_in_aoi_count}")
print(f"Loss Percentage: {spi_to_aoi_loss_pct:.2f}%")

print(f"\nExtra In AOI   : {extra_in_aoi_count}")
print(f"Extra Percentage: {aoi_extra_pct:.2f}%")

print("\nReport saved:")
print("reports/reconciliation_report.json")
print("reports/reconciliation_report.txt")

print("\nKafka Reconciliation Completed")
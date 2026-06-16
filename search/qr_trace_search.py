import subprocess

qr_code = input("Enter QR Code: ").strip()

result = subprocess.run(
    ["rg", qr_code, "sample-data/"],
    capture_output=True,
    text=True
)

spi_found = "spi_data.csv" in result.stdout
aoi_found = "aoi_data.csv" in result.stdout
fcr_found = "fcr_data.csv" in result.stdout

print("\n================================")
print("TRACEABILITY REPORT")
print("================================")

print(f"QR Code : {qr_code}")

print(f"SPI : {'FOUND' if spi_found else 'NOT FOUND'}")
print(f"AOI : {'FOUND' if aoi_found else 'NOT FOUND'}")
print(f"FCR : {'FOUND' if fcr_found else 'NOT FOUND'}")

print("\nSTATUS")

if spi_found and aoi_found and fcr_found:
    print("Passed All Stages")

elif spi_found and aoi_found and not fcr_found:
    print("Missing Between AOI and FCR")

elif spi_found and not aoi_found:
    print("Missing Between SPI and AOI")

else:
    print("QR Not Found")   
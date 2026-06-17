from dotenv import dotenv_values

config = dotenv_values("config.env")

print("Raw Config:")
print(config)

line_config = {}

for key, value in config.items():
    line_config[key] = value.split(",")

print("\nParsed Config:")
print(line_config)
from dotenv import dotenv_values

config = dotenv_values("config.env")

topics = []

topics.extend(config["AOI_TOPICS"].split(","))
topics.extend(config["SPI_TOPICS"].split(","))
topics.extend(config["FCR_TOPICS"].split(","))

for topic in topics:
    # execute kafka-topics --create
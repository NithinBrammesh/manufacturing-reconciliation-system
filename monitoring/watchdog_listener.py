import time
import subprocess

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class CSVHandler(FileSystemEventHandler):

    def run_pipeline(self, file_path):

        print("\n================================")
        print("CSV EVENT DETECTED")
        print(file_path)
        print("================================")

        try:

            # SPI File Detected
            if "SPI1" in file_path:

                print("\nRunning SPI Producer...\n")

                subprocess.run(
                    ["python3", "kafka-producer/spi_producer.py"],
                    check=True
                )

            # AOI File Detected
            elif "AOI3D1" in file_path:

                print("\nRunning AOI Producer...\n")

                subprocess.run(
                    ["python3", "kafka-producer/aoi_producer.py"],
                    check=True
                )

            else:

                print("Unknown folder. Skipping...")
                return

            print("\nRunning SPI Consumer...\n")

            subprocess.run(
                ["python3", "kafka-consumer/spi_consumer.py"],
                check=True
            )

            print("\nRunning AOI Consumer...\n")

            subprocess.run(
                ["python3", "kafka-consumer/aoi_consumer.py"],
                check=True
            )

            print("\nRunning Kafka Reconciliation...\n")

            subprocess.run(
                [
                    "python3",
                    "reconciliation-engine/kafka_reconciliation.py"
                ],
                check=True
            )

            print("\n================================")
            print("PIPELINE COMPLETED")
            print("================================\n")

        except Exception as e:

            print("\nPipeline Failed")
            print(str(e))

    # New file added
    def on_created(self, event):

        if event.is_directory:
            return

        if not event.src_path.lower().endswith(".csv"):
            return

        print("\nNEW CSV FILE DETECTED")

        self.run_pipeline(event.src_path)

    # File deleted
    def on_deleted(self, event):

        if event.is_directory:
            return

        if not event.src_path.lower().endswith(".csv"):
            return

        print("\nCSV FILE DELETED")

        self.run_pipeline(event.src_path)


if __name__ == "__main__":

    path_to_watch = "real-data"

    event_handler = CSVHandler()

    observer = Observer()

    observer.schedule(
        event_handler,
        path=path_to_watch,
        recursive=True
    )

    observer.start()

    print("\n================================")
    print("WATCHDOG STARTED")
    print("Watching: real-data")
    print("================================\n")

    try:

        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        print("\nStopping Watchdog...")

        observer.stop()

    observer.join()
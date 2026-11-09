# test mode for user testing
# run "python main.py test" and every command the app sends gets saved to a csv
# in the logs folder, during the test press M when the app missed a gesture
# and F when the app did something the person didn't mean

import csv
import time
from datetime import datetime
from pathlib import Path

log_file = None
writer = None
start = 0.0
counts = {}


def start_log():
    global log_file, writer, start
    folder = Path(__file__).with_name("logs")
    folder.mkdir(exist_ok=True)
    name = datetime.now().strftime("session_%Y-%m-%d_%H-%M-%S.csv")
    log_file = open(folder / name, "w", newline="")
    writer = csv.writer(log_file)
    writer.writerow(["seconds", "event", "detail"])
    start = time.monotonic()
    print(f"Test mode on, logging to logs/{name}")
    print("Press M when a gesture gets missed and F when the app does something it shouldn't")


def log_event(event, detail=""):
    # does nothing unless test mode is on
    if writer is None:
        return
    writer.writerow([f"{time.monotonic() - start:.1f}", event, detail])
    log_file.flush()
    counts[event] = counts.get(event, 0) + 1


def stop_log():
    if log_file is None:
        return
    log_file.close()
    print("Test summary")
    for event, count in counts.items():
        print(f"  {event}: {count}")

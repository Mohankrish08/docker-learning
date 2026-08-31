
import time
from datetime import datetime

while True:
    line = f"Hello from the writer at {datetime.now():%H:%M:%S}"

    # "a" means append — add to the end, don't erase what's there
    with open("/data/messages.txt", "a") as f:
        f.write(line + "\n")

    print("wrote:", line)
    time.sleep(5)

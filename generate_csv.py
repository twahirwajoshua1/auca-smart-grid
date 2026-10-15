import csv
import time
import smart_meter_simulator as sim

info = sim.dataset_info()
print("Expected counts:", info["expected_counts"])
print("Planned readings:", info["planned_readings"])

fields = info["reading_fields"]
start = time.time()
count = 0

with open("readings.csv", "w", newline="") as f:
    w = csv.writer(f)
    for r in sim.iter_readings():
        w.writerow([r[k] for k in fields])
        count += 1
        if count % 500000 == 0:
            print("Consumed so far:", count, "| elapsed s:", round(time.time() - start))

secs = round(time.time() - start, 1)
print("FINAL dictionaries consumed:", count)
print("Expected emitted_readings:", info["expected_counts"]["emitted_readings"])
print("CSV generation seconds:", secs)

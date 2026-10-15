import json
import time
import itertools
import paho.mqtt.client as mqtt
import smart_meter_simulator as sim

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="pub1")
client.connect("localhost", 1884)
client.loop_start()

taken = 0
infos = []

for reading in itertools.islice(sim.iter_readings(), 2000):
    taken += 1
    topic = f"energy/meters/{reading['meter_id']}"
    info = client.publish(topic, json.dumps(reading), qos=1, retain=False)
    infos.append(info)
    time.sleep(0.02)

for info in infos:
    info.wait_for_publish()

acked = sum(1 for i in infos if i.is_published())

print("Taken from generator:", taken)
print("Acknowledged by broker:", acked)

client.loop_stop()
client.disconnect()

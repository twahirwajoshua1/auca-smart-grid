import json
import psycopg2
import paho.mqtt.client as mqtt

conn = psycopg2.connect(host="localhost", port=5432, dbname="auca_energy",
                        user="postgres", password="YOUR_PASSWORD")
conn.autocommit = True
cur = conn.cursor()
cur.execute("SET synchronous_commit TO off")

received = 0
failed = 0

def on_message(client, userdata, msg):
    global received, failed
    received += 1
    try:
        r = json.loads(msg.payload)
        cur.execute(
            """INSERT INTO energy_live VALUES
               (%(meter_id)s, %(event_time)s, %(received_time)s, %(power_kw)s,
                %(voltage_v)s, %(current_a)s, %(frequency_hz)s, %(energy_kwh)s)""",
            r,
        )
    except Exception as e:
        failed += 1
        print("Insert error:", e)
    if received % 200 == 0:
        print("Received so far:", received, "| failed:", failed)
    if received >= 2000:
        print("FINAL received:", received, "| failed inserts:", failed)
        client.disconnect()

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="sub2",
                     clean_session=True)
client.on_message = on_message
client.connect("localhost", 1884)
client.subscribe("energy/meters/#", qos=1)
print("Subscriber ready. It stops by itself after 2000 messages.")
client.loop_forever()

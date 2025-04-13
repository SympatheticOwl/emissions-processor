# Use this client to publish a single row of data for each configured vehicle
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import os
import time
import json
import pandas as pd

# Starting and end index
device_st = 0
device_end = 5  # Reduced to 5 devices for testing

# Path to the dataset
data_path = "v_data/vehicle{}.csv"  # Path to vehicle CSV files

# Path to your certificates
certificate_formatter = "./certificates/devices/device_{}.cert.pem"
key_formatter = "./certificates/devices/device_{}.private.key"

iot_endpoint = os.getenv("iot_endpoint")

class MQTTClient:
    def __init__(self, device_id, cert, key):
        # For certificate based connection
        self.device_id = str(device_id)
        self.state = 0
        self.client = AWSIoTMQTTClient(self.device_id)
        # Update with your endpoint
        self.client.configureEndpoint(iot_endpoint, 8883)
        self.client.configureCredentials("./certificates/AmazonRootCA1.pem", key, cert)
        self.client.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
        self.client.configureDrainingFrequency(2)  # Draining: 2 Hz
        self.client.configureConnectDisconnectTimeout(10)  # 10 sec
        self.client.configureMQTTOperationTimeout(5)  # 5 sec
        self.client.onMessage = self.customOnMessage

    def customOnMessage(self, message):
        print("client {} received payload {} from topic {}".format(
            self.device_id,
            message.payload,
            message.topic
        ))

    # Suback callback
    def customSubackCallback(self, mid, data):
        # You don't need to write anything here
        print("Subscribed to topic successfully")

    # Puback callback
    def customPubackCallback(self, mid):
        # You don't need to write anything here
        print("Published message successfully")

    def subscribe(self):
        # Subscribe to the analysis topic for this device
        topic = f"vehicle/emission/analysis/{self.device_id}"
        print(f"Device {self.device_id} - Subscribing to {topic}")
        # self.client.subscribe(topic, 0, self.customOnMessage)
        self.client.subscribeAsync(topic, 0, ackCallback=self.customSubackCallback)


    def publish(self, topic="vehicle/emission/data/{}"):
        try:
            formatted_topic = topic.format(self.device_id)
            # Load the vehicle's emission data
            df = pd.read_csv(data_path.format(self.device_id))

            # Only publish one row at a time
            if len(df) > 0:
                row = df.iloc[self.state % len(df)]
                print(f">>> printing row: [{row}]")

                # Create JSON payload
                payload = {
                    "device_id": self.device_id,
                    "timestep_time": row.get('timestep_time', 0),
                    "timestamp": time.time(),
                    "vehicle_id": row.get('vehicle_id', 0),
                    "vehicle_CO": row.get('vehicle_CO', 0),
                    "vehicle_CO2": row.get('vehicle_CO2', 0),
                    "vehicle_HC": row.get('vehicle_HC', 0),
                    "vehicle_NOx": row.get('vehicle_NOx', 0),
                    "vehicle_PMx": row.get('vehicle_PMx', 0),
                    "vehicle_speed": row.get('vehicle_speed', 0),
                    "vehicle_noise": row.get('vehicle_noise', 0),
                    "vehicle_fuel": row.get('vehicle_fuel', 0),
                    "vehicle_x": row.get('vehicle_x', 0),
                    "vehicle_y": row.get('vehicle_y', 0)
                }

                # Publish the payload
                print(f"Device {self.device_id} - Publishing to {formatted_topic}")
                self.client.publishAsync(
                    formatted_topic,
                    json.dumps(payload),
                    0,
                    ackCallback=self.customPubackCallback
                )

                # Increment state for next message
                self.state += 1

                # Sleep to simulate real-time data
                time.sleep(0.5)  # 500ms delay between messages
            else:
                print(f"No data available for device {self.device_id}")
        except Exception as e:
            print(f"Error publishing data for device {self.device_id}: {e}")


print("Loading vehicle data...")
data = []
for i in range(device_st, device_end):
    try:
        a = pd.read_csv(data_path.format(i))
        data.append(a)
        print(f"Loaded data for vehicle {i}")
    except Exception as e:
        print(f"Could not load data for vehicle {i}: {e}")

print("Initializing MQTTClients...")
clients = []
for device_id in range(device_st, device_end):
    try:
        # Format certificate and key paths correctly
        cert_path = certificate_formatter.format(device_id)
        key_path = key_formatter.format(device_id)

        print(f"Creating client for device {device_id}")
        client = MQTTClient(device_id, cert_path, key_path)

        # Connect and subscribe
        client.client.connect()
        client.subscribe()
        clients.append(client)
    except Exception as e:
        print(f"Error initializing device {device_id}: {e}")

print(f"Successfully initialized {len(clients)} devices")

while True:
    print("\nOptions:")
    print("  's' to send data from all devices")
    print("  'd' to disconnect all devices and exit")
    print("  'q' to exit without disconnecting")

    x = input("Enter command: ")

    if x == "s":
        print(f"Sending data from {len(clients)} devices...")
        for c in clients:
            c.publish()
    elif x == "d":
        for c in clients:
            c.client.disconnect()
        print("All devices disconnected")
        exit()
    elif x == "q":
        print("Exiting without disconnecting")
        exit()
    else:
        print("Invalid command")

    time.sleep(1)
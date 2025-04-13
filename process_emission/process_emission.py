import json
import logging
import sys
import time
import traceback
from threading import Timer

import awsiot.greengrasscoreipc
import awsiot.greengrasscoreipc.client as client
from awsiot.greengrasscoreipc.model import (
    QOS,
    PublishToIoTCoreRequest,
    SubscribeToIoTCoreRequest
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)

# Keep track of max CO2 values for each device
maxco2 = {}

TIMEOUT = 10
DATA_TOPIC = "vehicle/emission/data"
ANALYSIS_TOPIC = "vehicle/emission/analysis"

ipc_client = awsiot.greengrasscoreipc.connect()

class StreamHandler(client.SubscribeToIoTCoreStreamHandler):
    def __init__(self):
        super().__init__()

    def on_stream_event(self, event):
        try:
            # Access the message using the correct attribute structure
            if hasattr(event, 'message'):
                # Parse message from message.payload
                message_string = str(event.message.payload, "utf-8")
                logger.info(f"Received message: {message_string}")

                # Parse the message
                message = json.loads(message_string)
                # Process the message
                process_message(message)
            else:
                logger.error(f"Unexpected message format: {event}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            logger.error(traceback.format_exc())

    def on_stream_error(self, error):
        logger.error(f"Stream error: {error}")

    def on_stream_closed(self):
        logger.info("Stream closed")


def process_message(message):
    """Process the emission data for a device."""
    device_id = message.get('device_id')
    co2_value = float(message.get('vehicle_CO2', 0))

    # Initialize max value for this device if not already present
    if device_id not in maxco2:
        maxco2[device_id] = 0

    # Update the max CO2 value if needed
    if co2_value > maxco2[device_id]:
        maxco2[device_id] = co2_value

    # Create response payload
    response = {
        "device_id": device_id,
        "max_CO2": maxco2[device_id],
        "current_CO2": co2_value,
        "timestamp": time.time(),
        "timestep_time": message.get('timestep_time', 0),
        "vehicle_id": message.get('vehicle_id', 0),
        "vehicle_CO": message.get('vehicle_CO', 0),
        "vehicle_CO2": message.get('vehicle_CO2', 0),
        "vehicle_HC": message.get('vehicle_HC', 0),
        "vehicle_NOx": message.get('vehicle_NOx', 0),
        "vehicle_PMx": message.get('vehicle_PMx', 0),
        "vehicle_speed": message.get('vehicle_speed', 0),
        "vehicle_noise": message.get('vehicle_noise', 0),
        "vehicle_fuel": message.get('vehicle_fuel', 0),
        "vehicle_x": message.get('vehicle_x', 0),
        "vehicle_y": message.get('vehicle_y', 0)
    }

    # Publish to the device-specific topic
    response_topic = f"{ANALYSIS_TOPIC}/{device_id}"
    publish_to_iot_core(response_topic, json.dumps(response))
    logger.info(f"Published to topic: {response_topic}, payload: {json.dumps(response)}")


def publish_to_iot_core(topic, message):
    """Publish a message to IoT Core."""
    try:
        request = PublishToIoTCoreRequest()
        request.topic_name = topic
        request.qos = QOS.AT_LEAST_ONCE
        request.payload = bytes(message, "utf-8")

        operation = ipc_client.new_publish_to_iot_core()
        operation.activate(request)
        future = operation.get_response()
        future.result(TIMEOUT)
    except Exception as e:
        logger.error(f"Failed to publish to topic {topic}: {e}")
        logger.error(traceback.format_exc())


def subscribe_to_topic():
    """Subscribe to the emission data topic."""
    try:
        request = SubscribeToIoTCoreRequest()
        request.topic_name = f"{DATA_TOPIC}/#"
        request.qos = QOS.AT_LEAST_ONCE

        handler = StreamHandler()
        operation = ipc_client.new_subscribe_to_iot_core(handler)
        future = operation.activate(request)
        future.result(TIMEOUT)

        logger.info(f"Successfully subscribed to topic: {DATA_TOPIC}/#")
    except Exception as e:
        logger.error(f"Failed to subscribe to topic {DATA_TOPIC}: {e}")
        logger.error(traceback.format_exc())


def main():
    """Main function to start the component."""
    try:
        logger.info("Emission Processor Component starting...")

        # Subscribe to emission data topic
        subscribe_to_topic()

        # Keep the component running
        while True:
            time.sleep(10)
    except Exception as e:
        logger.error(f"Exception occurred: {e}")
        logger.error(traceback.format_exc())
        exit(1)


if __name__ == "__main__":
    main()


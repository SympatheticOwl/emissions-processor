import json
import logging
import sys
import time
import traceback
import os
import boto3

import awsiot.greengrasscoreipc
import awsiot.greengrasscoreipc.client as client
from awsiot.greengrasscoreipc.model import (
    QOS,
    SubscribeToIoTCoreRequest
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)

# Firehose configurations
DELIVERY_STREAM_NAME = "emissions-stream"
TOPIC = "vehicle/emission/analysis/#"
TIMEOUT = 10

# Initialize clients
ipc_client = awsiot.greengrasscoreipc.connect()

# Use environment variables for AWS credentials
aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
aws_region = os.environ.get('AWS_REGION', 'us-east-2')

logger.info(f"AWS configuration - Region: {aws_region}, Access Key Present: {aws_access_key is not None}, Secret Key Present: {aws_secret_key is not None}")

# Initialize Firehose client with explicit credentials
firehose_client = boto3.client(
    'firehose',
    region_name=aws_region,
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key
)

class StreamHandler(client.SubscribeToIoTCoreStreamHandler):
    def __init__(self):
        super().__init__()

    def on_stream_event(self, event):
        try:
            # Debug log to see the full event structure
            logger.info(f"Received event: {event}")
            
            # For IoTCoreMessage, the message is directly available in the payload
            # This handles both v1 and v2 of the SDK
            if hasattr(event, 'binary_message'):
                message_string = str(event.binary_message.message, "utf-8")
            elif hasattr(event, 'message'):
                message_string = str(event.message.payload, "utf-8")
            else:
                message_string = str(event.payload, "utf-8")
                
            logger.info(f"Received message: {message_string}")

            # Parse the message
            message = json.loads(message_string)
            
            # Send to Firehose
            send_to_firehose(message)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            logger.error(traceback.format_exc())

    def on_stream_error(self, error):
        logger.error(f"Stream error: {error}")

    def on_stream_closed(self):
        logger.info("Stream closed")

def send_to_firehose(record):
    """Send data to Firehose delivery stream."""
    try:
        # Add timestamp if not present
        if 'timestamp' not in record:
            record['timestamp'] = time.time()
            
        # Convert the record to JSON string
        data = json.dumps(record) + '\n'  # Add newline delimiter for easier parsing

        # Send to Firehose
        response = firehose_client.put_record(
            DeliveryStreamName=DELIVERY_STREAM_NAME,
            Record={'Data': data.encode('utf-8')}
        )
        
        logger.info(f"Successfully sent to Firehose: {record.get('device_id')} - RecordId: {response.get('RecordId')}")
    except Exception as e:
        logger.error(f"Failed to send to Firehose: {e}")
        logger.error(traceback.format_exc())

def subscribe_to_topic():
    """Subscribe to the emission analysis topic."""
    try:
        request = SubscribeToIoTCoreRequest()
        request.topic_name = TOPIC
        request.qos = QOS.AT_LEAST_ONCE

        handler = StreamHandler()
        operation = ipc_client.new_subscribe_to_iot_core(handler)
        future = operation.activate(request)
        future.result(TIMEOUT)

        logger.info(f"Successfully subscribed to topic: {TOPIC}")
    except Exception as e:
        logger.error(f"Failed to subscribe to topic {TOPIC}: {e}")
        logger.error(traceback.format_exc())

def main():
    """Main function to start the component."""
    try:
        logger.info("Firehose Emissions Component starting...")

        # Subscribe to emission analysis topic
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

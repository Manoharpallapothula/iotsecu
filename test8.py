import paho.mqtt.client as mqtt
import ssl
import time
import json
import _thread
import asyncio
from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import Message
from pymongo import MongoClient
import board
import Adafruit_DHT
from datetime import datetime
from google.cloud import pubsub_v1

# Constants
MONGO_URI = "mongodb+srv://test:test@cluster0.wwz3l5h.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MONGO_DB_NAME = "sensor"
MONGO_COLLECTION_NAME = "time_tem_hum"
AZURE_CONN_STR = "HostName=rasp-iothub.azure-devices.net;DeviceId=data;SharedAccessKey=PuXkIMWO3o9rIAiz1eOZCSNlSfipIgU/fAIoTHhLrDA="
GOOGLE_PROJECT_ID = "cloud-425008"
GOOGLE_TOPIC_NAME = "raspidata"
keyfile_path = "./googlekey.json"

# Functions
def read_sensor_data():
    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, 17)
    if humidity is not None and temperature is not None:
        return temperature, humidity
    else:
        print("Failed to read sensor data.")
        return None, None

def on_connect(client, userdata, flags, rc):
    print("Connected to AWS IoT: " + str(rc))

async def publish_to_azure(temperature, humidity, mongo_collection):
    async def send_recurring_telemetry(device_client):
        cloud = "Azure"
        await device_client.connect()
        while True:
            msg_txt_formatted = '{{"timestamp": "{}", "temperature": {}, "humidity": {}}}'.format(datetime.now().isoformat(), temperature, humidity)
            message = Message(msg_txt_formatted)
            message.content_encoding = "utf-8"
            message.content_type = "application/json"
            print("Sending message to Azure - " + msg_txt_formatted)
            await device_client.send_message(message)
            mongo_collection.insert_one({"Cloud": cloud, "timestamp": datetime.now(), "temperature": temperature, "humidity": humidity})
            await asyncio.sleep(10)

    device_client = IoTHubDeviceClient.create_from_connection_string(AZURE_CONN_STR)
    try:
        await send_recurring_telemetry(device_client)
    except KeyboardInterrupt:
        print("User initiated exit")
    finally:
        await device_client.shutdown()

def publish_to_google_cloud(temperature, humidity, mongo_collection):
    cloud = "Google"
    publisher = pubsub_v1.PublisherClient.from_service_account_file(keyfile_path)
    topic_path = publisher.topic_path(GOOGLE_PROJECT_ID, GOOGLE_TOPIC_NAME)
    while True:
        try:
            data = '{{"timestamp": "{}", "temperature": {}, "humidity": {}}}'.format(datetime.now().isoformat(), temperature, humidity)
            print("Publishing data to Google Cloud:", data)  # Print the data being published
            publisher.publish(topic_path, data.encode())
            mongo_collection.insert_one({"Cloud": cloud, "timestamp": datetime.now(), "temperature": temperature, "humidity": humidity})
            time.sleep(10)
        except KeyboardInterrupt:
            print("User initiated exit")
            break

def main():
    mongo_client = MongoClient(MONGO_URI)
    mongo_db = mongo_client[MONGO_DB_NAME]
    mongo_collection = mongo_db[MONGO_COLLECTION_NAME]
    print("Select cloud platform:")
    print("1. AWS")
    print("2. Azure")
    print("3. Google Cloud")
    choice = input("Enter your choice: ")

    if choice == "1": # AWS
        cloud = "AWS"
        client = mqtt.Client()
        client.on_connect = on_connect
        client.tls_set(ca_certs='./AmazonRootCA11.pem', certfile='./certificate1.pem.crt', keyfile='./private1.pem.key',cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2)
        #client.tls_insecure_set(True)
        client.connect("a2axn9ibwlfeel-ats.iot.us-east-1.amazonaws.com", 8883, 60)
        try:
            while True:
                temperature, humidity = read_sensor_data()
                if temperature is not None and humidity is not None:
                    payload = {
                        "timestamp": datetime.now().isoformat(),
                        "temperature": temperature,
                        "humidity": humidity
                    }
                    payload_json = json.dumps(payload)
                    print("Publishing data to AWS:", payload_json)
                    client.publish("777", payload_json, qos=0, retain=False)
                    mongo_collection.insert_one({"Cloud": cloud, "timestamp": datetime.now(), "temperature": temperature, "humidity": humidity})
                    time.sleep(10)
        except KeyboardInterrupt:
            print("Keyboard interruption detected. Stopping AWS data publishing.")
            aws_client.disconnect()
            aws_client.loop_stop()
    elif choice == "2": # Azure
        temperature, humidity = read_sensor_data()
        if temperature is not None and humidity is not None:
            asyncio.run(publish_to_azure(temperature, humidity, mongo_collection))
        else:
            print("Failed to read sensor data.")
    elif choice == "3": # Google Cloud
        temperature, humidity = read_sensor_data()
        if temperature is not None and humidity is not None:
            publish_to_google_cloud(temperature, humidity, mongo_collection)
        else:
            print("Failed to read sensor data.")
    else:
        print("Invalid choice. Please enter either '1', '2', or '3'.")

if __name__ == "__main__":
    main()

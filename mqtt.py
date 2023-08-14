import base64
import json
import os
import random
from paho.mqtt import client as mqtt_client
import pandas as pd
import numpy as np
import keyboard
import sys

# ip address for connecting to raspberry
broker = "192.168.1.48"
port = 1883
username = "dwmuser"
password = "dwmpass"

# topic is the format which knows how to receive a message.
# all messages will start with dwm/
topic = "#"
client_id = f"mqtt-{random.randint(0, 1000)}"

pos_df = pd.DataFrame()
data_df = pd.DataFrame()

def grouping_frame_tag(dataframe: pd.DataFrame):
    pos_frame_grouped = dataframe.groupby('superFrameNumber')
    pos_groups = pos_frame_grouped.groups

    pos_frame_tag = []
    for frame, indexes in pos_groups.items():
        for ind in indexes:
            pos_frame_tag.append(str(frame) + dataframe['Tag'].iloc[ind][-2:])

    dataframe['frame_tag'] = pos_frame_tag
    return dataframe

def main():
    global pos_df, data_df
    print("Press 'Esc' key to exit.")

    client = connect_mqtt()
    subscribe(client)
    client.loop_start()

    while True:
        if keyboard.is_pressed('esc'):

            pos_df = grouping_frame_tag(pos_df)
            data_df = grouping_frame_tag(data_df)

            log = pd.merge(data_df, pos_df)
            log['Time (ms)'] = log.groupby('Tag')['Time (ms)'].transform(lambda x: x - x.min()) / 1000
            log.drop(columns=['superFrameNumber'], inplace=True)

            log.rename(columns={'x': 'X', 'y': 'Y', 'z': 'Z', 'quality': 'Quality'}, inplace=True)
            log.index = log.index + 1

            num_tag = log['Tag'].nunique()
            num_anch = log['Number of Anchors'].iloc[0]
            rand_num = random.randint(1, 100000)

            file_name = f'log_{num_tag}_{num_anch}_{rand_num}.xlsx'
            outdir = './logs'
            if not os.path.exists(outdir):
                os.mkdir(outdir)

            full_path = os.path.join(outdir, file_name)
            log.to_excel(full_path)
            print(log)
            print(file_name)
            client.unsubscribe('#')
            client.loop_stop()
            sys.exit()


# Function to establish the MQTT connection
def connect_mqtt():
    def on_connect(client: mqtt_client.Client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    # Create an MQTT client instance
    client = mqtt_client.Client(client_id)
    # Set username and password for authentication
    client.username_pw_set(username, password)
    # Set the on_connect callback, sends the user message and check connection
    client.on_connect = on_connect
    # connect to the broker
    client.connect(broker, port)
    return client

# Function to subscribe to a topic and handle incoming messages
def subscribe(client: mqtt_client.Client):
    def on_message(client, userdata, msg):
        global pos_df, data_df
        payload = json.loads(msg.payload)
        node = msg.topic[9:13]

        if "position" in payload:
            pos = payload["position"]
            pos['superFrameNumber'] = payload['superFrameNumber']
            for dim in ('x', 'y', 'z'):
                pos[dim] = round(float(pos[dim]), 2)
            pos['Tag'] = node

            pos_df = pd.concat([pos_df, pd.DataFrame([pos])], ignore_index=True)

        elif "data" in payload:
            bytes = base64.b64decode(payload["data"])
            count = bytes[0]
            timestamp = int.from_bytes(bytes[1:5], "little")
            bytes = bytes[5:]
            data = {
                hex(
                    int.from_bytes(bytes[6 * i: 2 + 6 * i], "little")
                ): f'{int.from_bytes(bytes[2 + 6 * i: 6 * (i + 1)], "little")}mm'
                for i in range(count)
            }
            print(f"node: {msg.topic[9:13]}, count: {count}, {data}, time (ms): {timestamp}")
            data_dict = {'superFrameNumber': payload['superFrameNumber'],
                         'Tag': node, 'Number of Anchors': count, 'Time (ms)': timestamp}
            data_dict.update(data)

            data_df = pd.concat([data_df, pd.DataFrame([data_dict])], ignore_index=True)

        else:
            print(f"Received `{payload}` from `{msg.topic}` topic")

    # set the format which will get the message(subscribe to the topic)
    client.subscribe(topic)
    # set the on_message callback, receives the topic every time its been sent
    client.on_message = on_message


if __name__ == "__main__":
    main()

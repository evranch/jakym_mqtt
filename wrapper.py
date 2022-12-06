import paho.mqtt.client as mqtt
import time
import subprocess
import signal
from threading import Thread
from queue import Queue, Empty

process_handle = 0

server = 'gateway.evranch'

def on_connect(client, userdata, flags, rc):
    print(f"Connected to server {rc}")
    mqtt_client.subscribe('music/#',qos=1)

def sighandler(signum, frame):
    print("Killing subprocess")
    process_handle.kill()
    exit()

def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line.decode('utf-8'))
    print("Thread died")
    out.close()

def on_message(client, userdata, msg):
    global process_handle
    print(msg.topic)
    if msg.topic == 'music/raw':
        print(msg.payload)
        process_handle.stdin.write(msg.payload+b'\n')
    elif msg.topic == 'music/youtube':
        process_handle.stdin.write(b'youtube '+msg.payload+b'\n')
    elif msg.topic == 'music/pause':
        process_handle.stdin.write(b'pause\n')
        mqtt_client.publish('music/state','Paused', qos=1, retain=True)
    elif msg.topic == 'music/play':
        process_handle.stdin.write(b'play\n')
        mqtt_client.publish('music/state','Playing', qos=1, retain=True)

signal.signal(signal.SIGTERM, sighandler)
signal.signal(signal.SIGINT, sighandler)

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(server, 1883, 60)
mqtt_client.loop_start()

process_handle = subprocess.Popen(['jakym'],stdout=subprocess.PIPE, stdin=subprocess.PIPE, close_fds=True, bufsize=0)
q = Queue()
qthread = Thread(target=enqueue_output, args=(process_handle.stdout, q))
qthread.daemon = True
qthread.start()

ready = False
while True:
    if process_handle.poll() is not None:
        print("jakym died, restarting")
        process_handle = subprocess.Popen(['jakym'],stdout=subprocess.PIPE, stdin=subprocess.PIPE, close_fds=True, bufsize=0)
        qthread = Thread(target=enqueue_output, args=(process_handle.stdout, q))
        qthread.daemon = True
        qthread.start()

    try:
        line = q.get_nowait()
    except Empty:
        time.sleep(1)
    else:
        print(line)
        if 'Currently Playing' in line:
            mqtt_client.publish('music/song',line[20:], qos=1, retain=True)
            mqtt_client.publish('music/state','Playing', qos=1, retain=True)
        elif 'Resuming' in line:
            mqtt_client.publish('music/song',line[11:], qos=1, retain=True)
        elif 'Downloading' in line:
            mqtt_client.publish('music/state',line, qos=1, retain=True)
#!/usr/bin/env python3
import psutil
import time
import paho.mqtt.client as mqtt
import GPUtil
import json
import socket
import os
import signal
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# === CONFIGURAZIONE ===
BROKER = os.getenv("MQTT_BROKER", "192.168.1.10")
PORT = int(os.getenv("MQTT_PORT", "1883"))
USERNAME = os.getenv("MQTT_USERNAME", "")
PASSWORD = os.getenv("MQTT_PASSWORD", "")
TOPIC_BASE = os.getenv("TOPIC_BASE", "pc")
INTERVAL = int(os.getenv("INTERVAL", "30"))
PC_NAME = os.getenv("PC_NAME") or socket.gethostname()  # Use hostname if empty
# =======================

# Global client variable
client = None

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    print("\n[INFO] Shutting down gracefully...")
    if client:
        try:
            client.loop_stop()
            client.disconnect()
        except:
            pass
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# MQTT callbacks
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"[MQTT] Connection successful (reason code: {reason_code})")
    else:
        print(f"[MQTT] Connection failed (reason code: {reason_code})")

def on_disconnect(client, userdata, flags, reason_code, properties):
    print(f"[MQTT] Disconnected (reason code: {reason_code})")

def on_publish(client, userdata, mid, reason_code, properties):
    print(f"[MQTT] Message published successfully (mid: {mid})")

print(f"[INFO] PC Metrics to Home Assistant MQTT Bridge")
print(f"[INFO] PC Name: {PC_NAME}")
print(f"[INFO] Connecting to MQTT broker at {BROKER}:{PORT}...")
print(f"[INFO] Topic base: {TOPIC_BASE}/{PC_NAME}/metrics")
print(f"[INFO] Update interval: {INTERVAL} seconds")

# Show authentication status
if USERNAME and PASSWORD:
    print(f"[INFO] Authentication: ENABLED (username: {USERNAME})")
else:
    print(f"[INFO] Authentication: DISABLED (anonymous connection)")

try:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=PC_NAME)

    # Set callbacks
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_publish = on_publish

    if USERNAME and PASSWORD:
        client.username_pw_set(USERNAME, PASSWORD)

    client.connect(BROKER, PORT)
    client.loop_start()  # Start network loop in background thread

    print(f"[SUCCESS] Connected to MQTT broker at {BROKER}:{PORT}")
    print(f"[INFO] Press Ctrl+C to stop")
except Exception as e:
    print(f"[ERROR] Failed to connect to MQTT broker at {BROKER}:{PORT}")
    print(f"[ERROR] {type(e).__name__}: {e}")
    print(f"[HINT] Check that:")
    print(f"  1. The MQTT broker is running at {BROKER}:{PORT}")
    print(f"  2. The IP address in .env file is correct")
    print(f"  3. Firewall allows connection to port {PORT}")
    print(f"  4. The broker is reachable: ping {BROKER}")
    raise

def get_metrics():
    data = {}

    # CPU Temperature
    temps = psutil.sensors_temperatures()
    cpu_temp = None
    if "coretemp" in temps:
        # Average across all cores
        vals = [t.current for t in temps["coretemp"] if hasattr(t, "current")]
        if vals:
            cpu_temp = round(sum(vals) / len(vals), 1)
    data["cpu_temp_c"] = cpu_temp

    # GPU (supports multiple NVIDIA GPUs)
    try:
        gpus = GPUtil.getGPUs()
        for i, gpu in enumerate(gpus):
            data[f"gpu{i}_temp_c"] = gpu.temperature
            data[f"gpu{i}_load_percent"] = round(gpu.load * 100, 1)
            # GPU Memory
            data[f"gpu{i}_memory_used_mb"] = round(gpu.memoryUsed, 1)
            data[f"gpu{i}_memory_total_mb"] = round(gpu.memoryTotal, 1)
            data[f"gpu{i}_memory_percent"] = round((gpu.memoryUsed / gpu.memoryTotal) * 100, 1)
    except Exception:
        pass

    # RAM
    mem = psutil.virtual_memory()
    data["ram_percent"] = round(mem.percent, 1)
    data["ram_used_gb"] = round(mem.used / (1024**3), 2)
    data["ram_total_gb"] = round(mem.total / (1024**3), 2)
    data["ram_available_gb"] = round(mem.available / (1024**3), 2)

    # Disks (all mounted partitions)
    for part in psutil.disk_partitions(all=False):
        # Skip snap, loop, and other virtual filesystems
        if part.mountpoint.startswith("/snap") or part.mountpoint.startswith("/loop"):
            continue
        if part.fstype in ['squashfs', 'tmpfs', 'devtmpfs']:
            continue

        try:
            usage = psutil.disk_usage(part.mountpoint)

            # Extract device name from /dev/sda1, /dev/nvme0n1p2, etc.
            device_name = part.device.split('/')[-1]

            # Add disk metrics with device names
            data[f"disk_{device_name}_percent"] = round(usage.percent, 1)
            data[f"disk_{device_name}_used_gb"] = round(usage.used / (1024**3), 2)
            data[f"disk_{device_name}_total_gb"] = round(usage.total / (1024**3), 2)
            data[f"disk_{device_name}_free_gb"] = round(usage.free / (1024**3), 2)
            data[f"disk_{device_name}_mountpoint"] = part.mountpoint
            data[f"disk_{device_name}_mounted"] = True

        except (PermissionError, OSError):
            continue

    # All disks (including unmounted) - only basic info available
    try:
        import subprocess
        import re

        # Get all block devices using lsblk
        result = subprocess.run(
            ['lsblk', '-b', '-o', 'NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE', '-J'],
            capture_output=True, text=True, timeout=5
        )

        if result.returncode == 0:
            import json as json_module
            lsblk_data = json_module.loads(result.stdout)

            for device in lsblk_data.get('blockdevices', []):
                # Process main disks (sda, sdb, nvme0n1, etc.)
                if device['type'] == 'disk':
                    disk_name = device['name']
                    disk_size_gb = round(device['size'] / (1024**3), 2)

                    # Add total disk size
                    data[f"disk_{disk_name}_total_size_gb"] = disk_size_gb

                    # Try to get disk temperature using smartctl (requires sudo/root)
                    try:
                        temp_result = subprocess.run(
                            ['sudo', 'smartctl', '-a', f'/dev/{disk_name}', '-j'],
                            capture_output=True, text=True, timeout=3
                        )
                        if temp_result.returncode in [0, 4]:  # 0=ok, 4=some SMART values exceeded
                            smart_data = json_module.loads(temp_result.stdout)

                            # For NVMe drives
                            if 'nvme_smart_health_information_log' in smart_data:
                                temp = smart_data['nvme_smart_health_information_log'].get('temperature')
                                if temp:
                                    data[f"disk_{disk_name}_temp_c"] = temp
                            # For SATA/SAS drives
                            elif 'temperature' in smart_data:
                                temp = smart_data['temperature'].get('current')
                                if temp:
                                    data[f"disk_{disk_name}_temp_c"] = temp
                    except:
                        # Temperature not available for this disk
                        pass

                # Process partitions
                for child in device.get('children', []):
                    if child['type'] == 'part':
                        part_name = child['name']
                        part_size_gb = round(child['size'] / (1024**3), 2)
                        mountpoint = child.get('mountpoint', '')
                        fstype = child.get('fstype', 'unknown')

                        # If not already tracked (unmounted partitions)
                        if f"disk_{part_name}_mounted" not in data:
                            data[f"disk_{part_name}_total_gb"] = part_size_gb
                            data[f"disk_{part_name}_mountpoint"] = mountpoint or "not_mounted"
                            data[f"disk_{part_name}_fstype"] = fstype
                            data[f"disk_{part_name}_mounted"] = False
                            # Note: used/free space CANNOT be determined for unmounted filesystems
                            # The filesystem must be mounted to read its metadata

    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception):
        # If lsblk fails, just continue with mounted disks only
        pass

    return data


while True:
    try:
        payload = get_metrics()
        topic = f"{TOPIC_BASE}/{PC_NAME}/metrics"

        # Publish message
        result = client.publish(topic, json.dumps(payload))

        # Log publishing attempt
        print(f"[INFO] Publishing to topic: {topic}")
        print(f"[DATA] {json.dumps(payload, indent=2)}")

        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"[INFO] Message queued for delivery (rc: {result.rc})")
        else:
            print(f"[WARNING] Publish may have failed (rc: {result.rc})")

        # Wait for next interval
        print(f"[INFO] Waiting {INTERVAL} seconds until next update...")
        time.sleep(INTERVAL)

    except Exception as e:
        print(f"[ERROR] Error in main loop: {type(e).__name__}: {e}")
        time.sleep(INTERVAL)

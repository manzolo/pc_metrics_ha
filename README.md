# PC Metrics to Home Assistant

Monitor your Linux PC hardware metrics in Home Assistant via MQTT. Get real-time data on CPU/GPU temperatures, RAM usage, disk space, and more.

![Home Assistant Dashboard](https://img.shields.io/badge/Home%20Assistant-Dashboard-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)

## Features

### 🔥 Temperature Monitoring
- **CPU Temperature** - Average across all cores
- **GPU Temperature** - NVIDIA GPU monitoring
- **Disk Temperatures** - NVMe and SATA drives via SMART

### 💾 System Resources
- **RAM Usage** - Percentage, used, total, and available (GB)
- **GPU Load & Memory** - NVIDIA GPU utilization and VRAM usage
- **Disk Space** - All mounted partitions with usage percentage and GB

### 🔍 Advanced Features
- **Automatic Disk Discovery** - Detects all disks (mounted and unmounted)
- **Multi-GPU Support** - Tracks multiple NVIDIA GPUs
- **Human-Readable Values** - GB/MB alongside percentages
- **MQTT Authentication** - Secure broker connection
- **Systemd Service** - Auto-start on boot
- **Comprehensive Logging** - Detailed error messages and debugging

## Screenshots
<img width="1664" height="810" alt="immagine" src="https://github.com/user-attachments/assets/d689f877-9031-4c8e-88fc-b2a6d2459f72" />

Your Home Assistant dashboard will show:
- Real-time temperature gauges with color coding
- Storage usage bars for all partitions
- Historical graphs (24h temperature and usage trends)
- GPU performance metrics
- All disk temperatures including unmounted drives

## Requirements

- **OS**: Linux (Ubuntu, Debian, Fedora, etc.)
- **Python**: 3.8+
- **Hardware**:
  - NVIDIA GPU (optional, for GPU metrics)
  - SMART-capable drives (for disk temperatures)
- **Home Assistant** with MQTT broker (Mosquitto)

## Quick Start

### 1. Install

```bash
git clone https://github.com/manzolo/pc_metrics_ha.git
cd pc_metrics_ha
make install
```

This will:
- Create virtual environment in `~/pc_metrics_ha`
- Install Python dependencies
- Install system packages (lm-sensors, smartmontools)
- Configure passwordless sudo for smartctl
- Set up systemd service
- Create .env configuration file

### 2. Configure

Edit the configuration file:

```bash
nano ~/pc_metrics_ha/.env
```

Update these values:

```env
MQTT_BROKER=homeassistant.lan    # Your Home Assistant IP
MQTT_PORT=1883
MQTT_USERNAME=your_mqtt_user
MQTT_PASSWORD=your_mqtt_password
TOPIC_BASE=pc
INTERVAL=30
PC_NAME=                          # Leave empty to auto-detect hostname
```

### 3. Hardware Setup

Detect CPU temperature sensors:

```bash
sudo sensors-detect
```

Answer **YES** to all prompts.

### 4. Test

Run a quick test:

```bash
make test
```

You should see:
```
[INFO] PC Metrics to Home Assistant MQTT Bridge
[INFO] PC Name: YourHostname
[INFO] Connecting to MQTT broker at homeassistant.lan:1883...
[SUCCESS] Connected to MQTT broker
[INFO] Publishing to topic: pc/YourHostname/metrics
[DATA] { ... metrics ... }
```

### 5. Start Service

```bash
make start
make status
```

## Home Assistant Setup

### Add MQTT Sensors

1. Copy `homeassistant_sensors.yaml` to your Home Assistant config directory
2. Edit `configuration.yaml`:

```yaml
mqtt:
  sensor: !include homeassistant_sensors.yaml
```

3. **Important**: Replace `pc-hostname` in `homeassistant_sensors.yaml` with your actual hostname
4. Restart Home Assistant

### Create Dashboard

1. Go to **Settings** → **Dashboards** → **Add Dashboard**
2. Choose "New dashboard from scratch"
3. Name it "PC Metrics"
4. Click three dots → **Edit Dashboard** → **Raw configuration editor**
5. Copy and paste content from `homeassistant_dashboard.yaml`
6. Click **Save**

See [HOME_ASSISTANT_SETUP.md](HOME_ASSISTANT_SETUP.md) for detailed instructions.

## Makefile Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make install` | Complete installation |
| `make test` | Test application (60 second dry run) |
| `make start` | Start systemd service |
| `make stop` | Stop systemd service |
| `make restart` | Restart systemd service |
| `make status` | Check service status |
| `make logs` | View service logs (follow mode) |
| `make uninstall` | Remove everything |
| `make clean` | Remove Python cache files |

## Metrics Published

### CPU
- `cpu_temp_c` - Temperature in Celsius

### GPU (per GPU)
- `gpu0_temp_c` - Temperature
- `gpu0_load_percent` - GPU utilization
- `gpu0_memory_used_mb` - VRAM used
- `gpu0_memory_total_mb` - Total VRAM
- `gpu0_memory_percent` - VRAM usage percentage

### RAM
- `ram_percent` - Usage percentage
- `ram_used_gb` - Used memory
- `ram_total_gb` - Total memory
- `ram_available_gb` - Available memory

### Disks (Mounted)
- `disk_{device}_percent` - Usage percentage
- `disk_{device}_used_gb` - Used space
- `disk_{device}_total_gb` - Total space
- `disk_{device}_free_gb` - Free space
- `disk_{device}_mountpoint` - Mount location
- `disk_{device}_mounted` - Mount status

Example: `disk_nvme0n1p2_percent`, `disk_sda1_used_gb`

### Disks (Unmounted)
- `disk_{device}_total_gb` - Total size
- `disk_{device}_fstype` - Filesystem type (ntfs, ext4)
- `disk_{device}_mountpoint` - "not_mounted"
- `disk_{device}_mounted` - false

### Disk Temperatures
- `disk_{device}_temp_c` - Physical disk temperature

Example: `disk_sda_temp_c`, `disk_nvme0n1_temp_c`

**Note**: Used/free space is **not available** for unmounted drives (filesystem must be mounted to read metadata).

## Configuration

All settings are in `~/pc_metrics_ha/.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `MQTT_BROKER` | MQTT broker hostname/IP | 192.168.1.10 |
| `MQTT_PORT` | MQTT broker port | 1883 |
| `MQTT_USERNAME` | MQTT username (optional) | - |
| `MQTT_PASSWORD` | MQTT password (optional) | - |
| `TOPIC_BASE` | MQTT topic prefix | pc |
| `INTERVAL` | Update interval (seconds) | 30 |
| `PC_NAME` | PC name override (empty = auto) | - |

## Troubleshooting

### Service Won't Start

Check service status and logs:
```bash
make status
make logs
```

Common issues:
- MQTT broker unreachable → Check `MQTT_BROKER` in .env
- Authentication failed → Add `MQTT_USERNAME` and `MQTT_PASSWORD`
- Permission denied → Ensure sudo is configured for smartctl

### No Disk Temperatures

Configure passwordless sudo for smartctl:
```bash
echo "$USER ALL=(ALL) NOPASSWD: /usr/sbin/smartctl" | sudo tee /etc/sudoers.d/pc-metrics-smartctl
sudo chmod 0440 /etc/sudoers.d/pc-metrics-smartctl
```

Or run `make install` which does this automatically.

### Sensors Show "Unavailable" in Home Assistant

1. Verify service is running: `make status`
2. Check MQTT topic matches your PC name
3. Test MQTT: `mosquitto_sub -h localhost -t "pc/#" -v`
4. Verify sensor names in Home Assistant Developer Tools → States

### CPU Temperature Shows None

Run sensor detection:
```bash
sudo sensors-detect
```

Then restart the service:
```bash
make restart
```

## Architecture

- **Main Script**: `pc_to_ha.py` - Collects metrics every 30 seconds
- **MQTT**: Publishes to topic `pc/{hostname}/metrics`
- **Systemd Service**: Auto-starts on boot, restarts on failure
- **Configuration**: `.env` file for easy customization

### Metric Collection
- CPU: `psutil.sensors_temperatures()` - coretemp sensor
- GPU: `GPUtil` - NVIDIA GPU via nvidia-smi
- RAM: `psutil.virtual_memory()` - System memory
- Disks: `psutil.disk_partitions()` + `lsblk` - All storage devices
- Temperatures: `smartctl` - SMART data via sudo

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Credits

Built with:
- [psutil](https://github.com/giampaolo/psutil) - System monitoring
- [paho-mqtt](https://github.com/eclipse/paho.mqtt.python) - MQTT client
- [GPUtil](https://github.com/anderskm/gputil) - GPU monitoring
- [python-dotenv](https://github.com/theskumar/python-dotenv) - Environment management


---

**Made with ❤️ for the Home Assistant community**

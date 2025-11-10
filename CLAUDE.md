# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based system metrics collector that sends PC hardware metrics (CPU temperature, GPU stats, RAM usage, disk usage) to Home Assistant via MQTT. It's designed to run as a systemd service on Linux systems with NVIDIA GPUs.

## Architecture

**Main Script: `pc_to_ha.py`**
- Infinite loop that collects and publishes metrics every 30 seconds (configurable via `INTERVAL`)
- Uses persistent MQTT connection to broker
- Publishes JSON payload to topic: `{TOPIC_BASE}/{PC_NAME}/metrics`
- Auto-detects hostname for multi-PC deployments

**Metric Collection Strategy:**
- CPU temperature: Reads from `coretemp` sensor via psutil, averages all core temps (°C)
- GPU metrics: Iterates all NVIDIA GPUs via GPUtil, tracks:
  - Temperature (°C)
  - Load percentage
  - Memory usage (MB) - used, total, and percentage
- RAM: Reports percentage, used/total/available in GB
- Disks: Auto-discovers ALL disks (mounted and unmounted):
  - **Mounted disks**: Full metrics (percentage, used/free/total GB, mountpoint)
  - **Unmounted disks**: Basic info only (total size, filesystem type, mount status)
  - **Physical disks**: Temperature (°C) via smartctl (requires sudo setup)
  - Excludes virtual filesystems (snap, loop, squashfs, tmpfs)
  - Uses device names: `/dev/sda1` → `disk_sda1_*`, `/dev/nvme0n1p2` → `disk_nvme0n1p2_*`
  - **Important**: Used/free space CANNOT be read for unmounted filesystems (requires mounting)

**Configuration:**
All configuration is managed via `.env` file (see `.env.example` for template):
- `MQTT_BROKER`: MQTT broker IP address (default: "192.168.1.10")
- `MQTT_PORT`: MQTT broker port (default: 1883)
- `MQTT_USERNAME`: MQTT authentication username (optional)
- `MQTT_PASSWORD`: MQTT authentication password (optional)
- `TOPIC_BASE`: Root MQTT topic (default: "pc")
- `INTERVAL`: Polling interval in seconds (default: 30)
- `PC_NAME`: Override hostname for MQTT topic (default: auto-detected hostname)

## Development Commands

**Using Makefile:**
```bash
make help              # Show all available commands
make install          # Complete installation (venv, deps, systemd service, .env)
make test             # Test application (runs for 60 seconds)
make start            # Start systemd service
make stop             # Stop systemd service
make restart          # Restart systemd service
make status           # Check service status
make logs             # View service logs (follow mode)
make uninstall        # Remove everything (service + installation directory)
make clean            # Remove Python cache files
```

**Installation workflow:**
```bash
make install          # Install everything
nano ~/pc_metrics/.env  # Configure MQTT settings
sudo sensors-detect   # Run sensor detection (answer YES to all)
make start            # Start the service
make status           # Verify it's running
```

## Dependencies

Core Python packages (installed via pip in venv):
- `psutil` - System metrics (CPU, RAM, disk, sensors)
- `paho-mqtt` - MQTT client
- `GPUtil` - NVIDIA GPU monitoring
- `python-dotenv` - Environment variable management

System packages:
- `lm-sensors` - Hardware sensor detection (required for CPU temp)
- `smartmontools` - Disk SMART monitoring (required for disk temperatures)
  - Requires passwordless sudo configuration (automated by `make install`)
  - See DISK_TEMPERATURE_SETUP.md for manual setup

## Key Implementation Details

**Sensor Availability:** CPU temperature returns `None` if `coretemp` sensor not found. GPU metrics silently skip if GPUtil fails (e.g., no NVIDIA GPU). Handle missing metrics in Home Assistant configurations.

**Disk Filtering:** The code explicitly skips virtual filesystems (snap, loop, squashfs, tmpfs) and handles `PermissionError` for inaccessible partitions. When adding disk filtering logic, follow this pattern.

**Multi-GPU Support:** GPU metrics use indexed keys (`gpu0_temp_c`, `gpu1_temp_c`, etc.). Home Assistant sensor configurations need to handle variable GPU counts.

**MQTT Topic Structure:** Single topic per PC with all metrics in one JSON payload. For per-metric topics, modify the publishing loop.

**Metric Naming Convention:**
- CPU: `cpu_temp_c` (°C)
- GPU: `gpu{N}_temp_c`, `gpu{N}_load_percent`, `gpu{N}_memory_used_mb`, `gpu{N}_memory_total_mb`, `gpu{N}_memory_percent`
- RAM: `ram_percent`, `ram_used_gb`, `ram_total_gb`, `ram_available_gb`
- Disk (mounted partitions): `disk_{device}_percent`, `disk_{device}_used_gb`, `disk_{device}_total_gb`, `disk_{device}_free_gb`, `disk_{device}_mountpoint`, `disk_{device}_mounted`
  - Example: `disk_sda1_percent`, `disk_nvme0n1p2_used_gb`, `disk_sda1_mountpoint`
- Disk (unmounted partitions): `disk_{device}_total_gb`, `disk_{device}_mountpoint`, `disk_{device}_fstype`, `disk_{device}_mounted`
  - Example: `disk_sda3_total_gb`, `disk_sda3_fstype` (ntfs), `disk_sda3_mounted` (false)
- Disk (physical drives): `disk_{device}_total_size_gb`, `disk_{device}_temp_c`
  - Example: `disk_sda_total_size_gb`, `disk_nvme0n1_temp_c`

**Human-Readable Values:** All metrics include both percentage and absolute values (GB/MB) for better Home Assistant integration. This allows creating sensors with proper units and formatting.

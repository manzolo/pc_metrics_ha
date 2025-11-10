# Home Assistant Dashboard Setup Guide

This guide will help you create a beautiful dashboard in Home Assistant to display your PC metrics.

## Prerequisites

- Home Assistant installed and running
- MQTT integration configured (Mosquitto broker)
- PC Metrics application running and publishing to MQTT

## Step 1: Configure MQTT Sensors

### Option A: Using configuration.yaml (Recommended)

1. Open your Home Assistant configuration directory
2. Edit `configuration.yaml`
3. Add or update the `mqtt:` section:

```yaml
mqtt:
  sensor: !include homeassistant_sensors.yaml
```

4. Copy `homeassistant_sensors.yaml` to your Home Assistant config directory

### Option B: Direct configuration.yaml

Alternatively, add the sensors directly in `configuration.yaml`:

```yaml
mqtt:
  sensor:
    # CPU Temperature
    - name: "PC CPU Temperature"
      state_topic: "pc/Ubuntu-I9/metrics"
      unit_of_measurement: "°C"
      value_template: "{{ value_json.cpu_temp_c }}"
      device_class: temperature
      state_class: measurement

    # ... (copy all sensors from homeassistant_sensors.yaml)
```

### Important: Update PC Name

Replace `Ubuntu-I9` with your actual PC name in:
- All `state_topic` values
- The MQTT topic must match what your PC publishes to

Find your PC name by running:
```bash
hostname
```

Or check the MQTT topic in the application logs.

## Step 2: Restart Home Assistant

After adding the sensor configuration:

1. Go to **Settings** → **System** → **Restart**
2. Or use Developer Tools → YAML → Check Configuration → Restart

## Step 3: Verify Sensors

1. Go to **Developer Tools** → **States**
2. Search for "PC" or "sensor.pc_"
3. You should see all your sensors with current values:
   - `sensor.pc_cpu_temperature`
   - `sensor.pc_gpu_temperature`
   - `sensor.pc_ram_usage`
   - `sensor.pc_disk_root_usage`
   - etc.

**Troubleshooting:**
- If sensors show "unavailable": Check MQTT connection and topic names
- If sensors don't appear: Check configuration.yaml syntax with YAML validator
- Check Home Assistant logs: **Settings** → **System** → **Logs**

## Step 4: Create Dashboard

### Method 1: Import Complete Dashboard (Easy)

1. Go to **Settings** → **Dashboards**
2. Click **"+ ADD DASHBOARD"**
3. Choose **"New dashboard from scratch"**
4. Name it: `PC Metrics`
5. Click the dashboard to open it
6. Click the **three dots menu (⋮)** in the top right
7. Select **"Edit Dashboard"**
8. Click **three dots menu** again → **"Raw configuration editor"**
9. **Delete all existing content**
10. Copy and paste the entire content from `homeassistant_dashboard.yaml`
11. Click **"Save"**
12. Click **"Done"** to exit edit mode

### Method 2: Create Cards Manually (Customizable)

You can also create individual cards:

#### Example: CPU Temperature Gauge

```yaml
type: gauge
entity: sensor.pc_cpu_temperature
name: CPU Temperature
min: 0
max: 100
severity:
  green: 0
  yellow: 60
  red: 80
```

#### Example: RAM Usage Bar

```yaml
type: entities
title: System Memory
entities:
  - entity: sensor.pc_ram_usage
    name: RAM Usage
  - entity: sensor.pc_ram_used
    name: Used
  - entity: sensor.pc_ram_available
    name: Available
```

#### Example: Disk Storage Card

```yaml
type: entities
title: Root Partition
entities:
  - entity: sensor.pc_disk_root_usage
    name: Usage Percentage
  - entity: sensor.pc_disk_root_used
    name: Used Space
  - entity: sensor.pc_disk_root_free
    name: Free Space
```

## Step 5: Optional Enhancements

### Install Custom Cards (Optional)

For better visualizations, install these custom cards via HACS:

1. **bar-card** - Beautiful progress bars for disk usage
   ```bash
   # Install via HACS
   HACS → Frontend → Explore & Download Repositories
   Search: "bar-card"
   ```

2. **mini-graph-card** - Compact graphs
3. **apexcharts-card** - Advanced charts

If you don't have HACS installed, the dashboard will work fine without custom cards (bar-card sections will be ignored).

### Create Automations

#### Example: High Temperature Alert

```yaml
automation:
  - alias: "PC High CPU Temperature Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.pc_cpu_temperature
        above: 80
    action:
      - service: notify.mobile_app
        data:
          title: "⚠️ High CPU Temperature"
          message: "PC CPU temperature is {{ states('sensor.pc_cpu_temperature') }}°C"
```

#### Example: Low Disk Space Alert

```yaml
automation:
  - alias: "PC Low Disk Space Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.pc_disk_root_usage
        above: 90
    action:
      - service: notify.mobile_app
        data:
          title: "⚠️ Low Disk Space"
          message: "Root partition is {{ states('sensor.pc_disk_root_usage') }}% full"
```

## Dashboard Features

### Overview Tab
- **Key Metrics Gauges**: CPU, GPU, RAM at a glance
- **CPU & GPU Details**: Temperatures and load
- **Memory Monitoring**: RAM usage with available/used breakdown
- **Storage Cards**: All mounted partitions with usage bars
- **Disk Temperatures**: Temperature gauges for all drives
- **Unmounted Disks**: Information about additional drives

### Details Tab
- **Temperature History**: 24-hour graphs
- **Usage History**: RAM, GPU, disk usage over time
- **Statistics**: 7-day min/max/average charts
- **All Sensors List**: Complete sensor overview

## Customization Tips

### Adjust Temperature Thresholds

Modify severity levels based on your hardware:

```yaml
severity:
  green: 0
  yellow: 60  # Change this
  red: 80     # Change this
```

### Change Time Ranges

Adjust history display:

```yaml
hours_to_show: 24  # Change to 12, 48, 72, etc.
days_to_show: 7    # Change to 3, 14, 30, etc.
```

### Add More Disks

If you have different disk names (sdc, sdd, etc.), copy sensor definitions:

```yaml
- name: "PC Disk SDC Temperature"
  state_topic: "pc/Ubuntu-I9/metrics"
  unit_of_measurement: "°C"
  value_template: "{{ value_json.disk_sdc_temp_c }}"
  device_class: temperature
```

### Organize Cards

Use `vertical-stack` and `horizontal-stack` to organize:

```yaml
type: horizontal-stack
cards:
  - type: gauge
    entity: sensor.pc_disk_nvme0_temperature
  - type: gauge
    entity: sensor.pc_disk_nvme1_temperature
```

## Troubleshooting

### Sensors Show "Unavailable"

1. Check MQTT broker is running:
   ```bash
   sudo systemctl status mosquitto
   ```

2. Verify PC metrics app is running:
   ```bash
   make status
   ```

3. Check MQTT topic matches:
   ```bash
   mosquitto_sub -h localhost -t "pc/#" -v
   ```

4. Verify sensor configuration in `configuration.yaml`

### Dashboard Not Loading

1. Check browser console for errors (F12)
2. Verify all entity IDs exist in Developer Tools → States
3. Check Home Assistant logs for YAML errors

### Missing Temperature Sensors

1. Ensure sudo is configured for smartctl:
   ```bash
   sudo -n smartctl -a /dev/sda
   ```

2. Check application logs:
   ```bash
   make logs
   ```

### Graphs Not Showing Data

- Wait a few minutes for data to accumulate
- Verify sensors are updating: Developer Tools → States
- Check recorder configuration includes your sensors

## Mobile App

The dashboard is fully responsive and works great on:
- Home Assistant mobile app (iOS/Android)
- Mobile browsers
- Tablets

## Screenshots

Your dashboard will display:
- 📊 Real-time gauges and charts
- 🌡️ Temperature monitoring with color coding
- 💾 Storage usage with visual bars
- 📈 Historical graphs
- 🔔 Optional alerts and notifications

## Next Steps

1. Set up automations for alerts
2. Customize colors and thresholds
3. Add to your main dashboard
4. Install custom cards for better visuals
5. Create notification rules

Enjoy your PC monitoring dashboard! 🎉

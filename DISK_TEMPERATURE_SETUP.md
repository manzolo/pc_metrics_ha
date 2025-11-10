# Disk Temperature Monitoring Setup

## Overview

The application now supports disk temperature monitoring for both NVMe and SATA drives using `smartctl` from smartmontools.

## Requirements

Disk temperature monitoring requires **sudo access** for smartctl because reading SMART data requires root privileges.

## One-Time Setup

Run this command **once** to configure passwordless sudo for smartctl:

```bash
echo "$USER ALL=(ALL) NOPASSWD: /usr/sbin/smartctl" | sudo tee /etc/sudoers.d/pc-metrics-smartctl
sudo chmod 0440 /etc/sudoers.d/pc-metrics-smartctl
```

Or simply run:
```bash
make install
```

This will be configured automatically during installation.

## What You Get

After setup, metrics will include:

### For each physical disk (sda, sdb, nvme0n1, etc.):
- `disk_sda_temp_c`: Temperature in Celsius
- `disk_nvme0n1_temp_c`: Temperature in Celsius

Example:
```json
{
  "disk_nvme0n1_temp_c": 45,
  "disk_nvme1n1_temp_c": 42,
  "disk_sda_temp_c": 38,
  "disk_sdb_temp_c": 35
}
```

## Important Limitations

### ❌ Used Space on Unmounted Drives

**It is IMPOSSIBLE to get used/free space for unmounted filesystems.**

Why? The filesystem metadata (which tracks used/free space) is only accessible when the filesystem is mounted. Without mounting:
- ✅ Can read: Total disk size
- ✅ Can read: Partition sizes
- ✅ Can read: Filesystem type (ntfs, ext4, etc.)
- ✅ Can read: Temperature (with smartctl)
- ❌ **Cannot read: Used space, free space, or usage percentage**

### Workaround

If you need to monitor unmounted drives' usage:

1. **Mount them temporarily**:
```bash
sudo mkdir -p /mnt/mydisk
sudo mount /dev/sda3 /mnt/mydisk
# Check space
df -h /mnt/mydisk
# Unmount
sudo umount /mnt/mydisk
```

2. **Auto-mount on boot** (add to /etc/fstab):
```bash
# Example for NTFS drive
/dev/sda3  /mnt/windows  ntfs  defaults,nofail  0  0
```

3. **Use a scheduled script** that mounts, reads space, unmounts (not recommended - causes wear)

## Testing

Test disk temperatures manually:
```bash
# NVMe drive
sudo smartctl -a /dev/nvme0n1 -j | python3 -c "import json, sys; d=json.load(sys.stdin); print(d['nvme_smart_health_information_log']['temperature'])"

# SATA drive
sudo smartctl -a /dev/sda -j | python3 -c "import json, sys; d=json.load(sys.stdin); print(d['temperature']['current'])"
```

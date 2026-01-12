# EVENTSEC Agent نصب (Linux)

## Prereqs
- systemd-based distro
- Go binary or packaged agent

## Install

1. Create directories:

```bash
sudo mkdir -p /etc/eventsec /var/lib/eventsec/state /var/log/eventsec
```

2. Create `/etc/eventsec/agent.yml`:

```yaml
server_url: https://<eventsec-backend>
enrollment_key: <enrollment-key>
heartbeat_interval: 30s
inventory_interval: 10m
log_level: info
max_spool_mb: 256
```

3. Install the binary:

```bash
sudo install -m 0755 eventsec-agent /usr/local/bin/eventsec-agent
```

4. Install systemd unit (see `agent/packaging/linux/eventsec-agent.service`) and enable:

```bash
sudo cp agent/packaging/linux/eventsec-agent.service /etc/systemd/system/eventsec-agent.service
sudo systemctl daemon-reload
sudo systemctl enable --now eventsec-agent
```

## Uninstall

```bash
sudo systemctl disable --now eventsec-agent
sudo rm -f /etc/systemd/system/eventsec-agent.service
sudo rm -f /usr/local/bin/eventsec-agent
sudo rm -rf /etc/eventsec /var/lib/eventsec
```

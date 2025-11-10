.PHONY: help install test uninstall start stop restart status logs clean

# Variables
INSTALL_DIR=$(HOME)/pc_metrics_ha
VENV=$(INSTALL_DIR)/venv
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip
SERVICE_NAME=pc_metrics.service
SERVICE_FILE=/etc/systemd/system/$(SERVICE_NAME)
CURRENT_USER=$(shell whoami)

help:
	@echo "PC Metrics to Home Assistant - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make install    - Install application, dependencies, and systemd service"
	@echo "  make test       - Test the application (dry run for 60 seconds)"
	@echo "  make uninstall  - Remove application and systemd service"
	@echo "  make start      - Start the systemd service"
	@echo "  make stop       - Stop the systemd service"
	@echo "  make restart    - Restart the systemd service"
	@echo "  make status     - Check systemd service status"
	@echo "  make logs       - View systemd service logs (follow mode)"
	@echo "  make clean      - Remove Python cache files"

install:
	@echo "Installing PC Metrics to Home Assistant..."
	@mkdir -p $(INSTALL_DIR)
	@echo "Creating virtual environment..."
	@python3 -m venv $(VENV)
	@echo "Installing Python dependencies..."
	@$(PIP) install --upgrade pip setuptools
	@$(PIP) install psutil paho-mqtt GPUtil python-dotenv
	@echo "Installing system dependencies..."
	@sudo apt-get update && sudo apt-get install -y lm-sensors smartmontools
	@echo "Configuring passwordless sudo for smartctl..."
	@echo "$(CURRENT_USER) ALL=(ALL) NOPASSWD: /usr/sbin/smartctl" | sudo tee /etc/sudoers.d/pc-metrics-smartctl > /dev/null
	@sudo chmod 0440 /etc/sudoers.d/pc-metrics-smartctl
	@echo "Copying application files..."
	@cp pc_to_ha.py $(INSTALL_DIR)/
	@cp .env.example $(INSTALL_DIR)/
	@if [ ! -f $(INSTALL_DIR)/.env ]; then \
		cp .env.example $(INSTALL_DIR)/.env; \
		echo "Created .env file - please edit $(INSTALL_DIR)/.env with your configuration"; \
	else \
		echo ".env file already exists, skipping..."; \
	fi
	@echo "Setting up systemd service..."
	@sed 's|tuoutente|$(CURRENT_USER)|g; s|/home/tuoutente|$(HOME)|g' pc_metrics.service > /tmp/$(SERVICE_NAME)
	@sudo cp /tmp/$(SERVICE_NAME) $(SERVICE_FILE)
	@sudo systemctl daemon-reload
	@sudo systemctl enable $(SERVICE_NAME)
	@echo ""
	@echo "Installation complete!"
	@echo "Next steps:"
	@echo "  1. Edit configuration: nano $(INSTALL_DIR)/.env"
	@echo "  2. Run sensor detection: sudo sensors-detect (answer YES to all)"
	@echo "  3. Start the service: make start"
	@echo "  4. Check status: make status"

test:
	@echo "Testing PC Metrics application..."
	@if [ ! -d $(VENV) ]; then \
		echo "Error: Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@if [ ! -f $(INSTALL_DIR)/.env ]; then \
		echo "Error: .env file not found. Copy .env.example to $(INSTALL_DIR)/.env and configure it."; \
		exit 1; \
	fi
	@echo "Running application for 60 seconds (press Ctrl+C to stop earlier)..."
	@cd $(INSTALL_DIR) && timeout 60 $(PYTHON) pc_to_ha.py || [ $$? -eq 124 ] && echo "Test completed successfully!"

uninstall:
	@echo "Uninstalling PC Metrics to Home Assistant..."
	@if [ -f $(SERVICE_FILE) ]; then \
		echo "Stopping and disabling systemd service..."; \
		sudo systemctl stop $(SERVICE_NAME) 2>/dev/null || true; \
		sudo systemctl disable $(SERVICE_NAME) 2>/dev/null || true; \
		sudo rm -f $(SERVICE_FILE); \
		sudo systemctl daemon-reload; \
	fi
	@echo "Removing sudoers configuration..."
	@sudo rm -f /etc/sudoers.d/pc-metrics-smartctl
	@echo "Removing installation directory..."
	@rm -rf $(INSTALL_DIR)
	@echo "Uninstallation complete!"

start:
	@echo "Starting PC Metrics service..."
	@sudo systemctl start $(SERVICE_NAME)
	@sudo systemctl status $(SERVICE_NAME) --no-pager

stop:
	@echo "Stopping PC Metrics service..."
	@sudo systemctl stop $(SERVICE_NAME)

restart:
	@echo "Restarting PC Metrics service..."
	@sudo systemctl restart $(SERVICE_NAME)
	@sudo systemctl status $(SERVICE_NAME) --no-pager

status:
	@sudo systemctl status $(SERVICE_NAME) --no-pager

logs:
	@echo "Showing PC Metrics service logs (Ctrl+C to exit)..."
	@journalctl -u $(SERVICE_NAME) -f

clean:
	@echo "Cleaning Python cache files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@echo "Clean complete!"

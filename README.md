# probe-request-logging
A lightweight application for Raspberry Pi devices designed to log nearby wireless probe requests. This can be useful for monitoring Wi-Fi activity and analyzing wireless network traffic in your environment.

## Required Equipment

- Raspberry Pi 3 Model B+ (or newer)
- MicroSD card with a fresh installation of Raspberry Pi OS Lite
- USB Wi-Fi adapter capable of monitor mode

## Installation

Follow these steps to install Probe Request Logging app on your Raspberry Pi as a background service:

1. Ensure your Raspberry Pi is running Raspberry Pi OS Lite and is connected to the internet.

2. Open a terminal and update your system:
```
sudo apt update
sudo apt -y upgrade
```
3. Clone the repository:
```
git clone git@github.com:alkenderesi/probe-request-logging.git
```
4. Change to the project directory:
```
cd probe-request-logging
```
5. Modify the MAC address in config.yaml to match your USB Wi-Fi adapter.

6. Make the installation script executable:
```
chmod +x install_service.sh
```
7. Run the installation script:
```
sudo ./install_service.sh
```
8. Check whether the service is running:
```
sudo systemctl status probe_request_logging.service
```

The script will install the necessary dependencies and configure the Probe Request Logging service to run automatically on startup.

## Usage

Once the installation is complete, the Probe Request Logging service will start automatically. The service logs probe requests detected by the USB Wi-Fi adapter to a csv file on the Raspberry Pi.

To control the service, you can use the standard `systemctl` commands. However the recommended way to stop the service is by shorting the GPIO pin specified in config.yaml to ground, which allows users to stop the service even without a display output or an input device.

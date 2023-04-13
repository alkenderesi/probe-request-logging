#!/bin/bash


SERVICE_NAME="Probe Request Logger"
SERVICE_FILE="probe_request_logger.service"
PYTHON_SCRIPT="probe_request_logger.py"
REQUIREMENTS_TXT="requirements.txt"

echo "Starting $SERVICE_NAME installation..."

echo -e "\nGathering directories"
current_dir=$(pwd)
python_dir=$(which python3)
echo "Current directory: $current_dir"
echo "Python directory: $python_dir"

echo -e "\nChecking $current_dir"
if [ ! -e "$current_dir/$PYTHON_SCRIPT" ] || [ ! -e "$current_dir/$REQUIREMENTS_TXT" ]
then
    echo -e "\nInstallation failed!"
    echo "Please run the installation script from the directory containing both $PYTHON_SCRIPT and $REQUIREMENTS_TXT"
    exit 1
fi

echo -e "\nInstalling pip3"
apt -y install python3-pip

echo -e "\nInstalling required python packages"
pip3 install -r $REQUIREMENTS_TXT

echo -e "\nCreating service file"
cat << EOF > /etc/systemd/system/$SERVICE_FILE
[Unit]
Description=$SERVICE_NAME
After=network.target

[Service]
User=root
WorkingDirectory=$current_dir
ExecStart=$python_dir $current_dir/$PYTHON_SCRIPT
Restart=no

[Install]
WantedBy=multi-user.target
EOF

echo -e "\nReloading systemd configuration"
systemctl daemon-reload

echo -e "\nEnabling the service to start on boot"
systemctl enable $SERVICE_FILE

echo -e "\nStarting service"
systemctl start $SERVICE_FILE

echo -e "\n$SERVICE_NAME has been installed and started successfully!"

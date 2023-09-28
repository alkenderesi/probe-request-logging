import os
import subprocess
import threading
import time
import datetime
import csv
import yaml
import scapy.all as scapy
import RPi.GPIO as GPIO


with open('config.yaml', 'r') as config_file:
    config = yaml.load(config_file, Loader=yaml.FullLoader)

GPIO.setmode(GPIO.BCM)
GPIO.setup(config['gpio_pin'], GPIO.IN, pull_up_down=GPIO.PUD_UP)

continue_sniff = True


def execute_command(command_args):
    # type: (list) -> str
    """
    Execute a shell command and return its stdout as a string.

    Args:
        command_args (list): List of arguments for the command.

    Returns:
        str: The stdout of the executed command.

    Raises:
        Exception: If the command returns a non-zero exit code.
    """

    result = subprocess.run(
        args=command_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        raise Exception(result.stderr)

    return result.stdout


def resolve_interface_id(mac_address):
    # type: (str) -> str
    """
    Resolves the ID of a network interface with the given MAC address.

    Args:
        mac_address (str): MAC address of the network interface.

    Returns:
        str: The ID of the network interface with the given
        MAC address.

    Raises:
        Exception: If no network interface with the given MAC address
        could be found.
    """

    mac_address = mac_address.lower()

    # bash -c: Execute the command in a subshell. This is necessary
    # because the pipe character | is a shell construct and not
    # part of the command itself.
    # ip -br link: List all network interfaces in a brief format.
    # grep -i: Search for the given pattern in the output of the
    # previous command. The -i flag makes the search case-insensitive.
    # awk '{print $1}': Print the first column of the output of the
    # previous command.

    command = [
        'bash', '-c',
        f"ip -br link | grep -i {mac_address} | awk '{{print $1}}'"
    ]

    interface_id = execute_command(command).strip()

    if not interface_id:
        raise Exception(
            f'No network interface with MAC address {mac_address}'
        )

    return interface_id


def set_interface_state(interface_id, enabled):
    # type: (str, bool) -> None
    """
    Enables/disables the network interface with the given interface ID.

    Args:
        interface_id (str): ID of the network interface.
        enabled (bool): True to enable the network interface, False to
        disable it.
    """

    # sudo: Execute the command as the superuser.
    # ifconfig: Configure network interfaces.
    # interface_id: ID of the network interface.
    # up/down: Enable/disable the network interface.

    command = [
        'sudo', 'ifconfig', interface_id,
        'up' if enabled else 'down'
    ]

    execute_command(command)


def enable_monitor_mode(interface_id):
    # type: (str) -> None
    """
    Enables monitor mode on the network interface with the given
    interface ID.

    Args:
        interface_id (str): ID of the network interface.
    """

    # sudo: Execute the command as the superuser.
    # iwconfig: Configure wireless network interfaces.
    # interface_id: ID of the network interface.
    # mode: Set the mode of the network interface.
    # monitor: Set the mode of the network interface to monitor mode.

    command = [
        'sudo', 'iwconfig', interface_id, 'mode', 'monitor'
    ]

    execute_command(command)


def check_gpio_pin_state():
    # type: () -> None
    """
    Checks the state of the chosen GPIO pin. If the pin is shorted to
    ground, continue_sniff is set to False and the sniffing process is
    terminated.
    """

    global continue_sniff

    while continue_sniff:

        if GPIO.input(config['gpio_pin']) == GPIO.LOW:
            continue_sniff = False

        time.sleep(config['gpio_check_frequency'])


def packet_handler(packet):
    # type: (scapy.Packet) -> None
    """
    Handles the given packet. This involves writing the current time,
    the source MAC address and the target SSID of the probe request
    to a csv log file.

    Args:
        packet (scapy.Packet): Packet to handle.
    """

    now = datetime.datetime.now()

    ssid = '*'
    for element in packet['Dot11Elt'].iterpayloads():
        if element.ID == 0:
            if element.len > 0:
                ssid = element.info.decode('utf-8', errors='ignore')
            elif config['ignore_wildcards']:
                return
            break

    src_mac = packet.addr2.lower()

    log_file_path = os.path.join(
        config['probe_request_log_directory'],
        now.strftime('%Y-%m-%d.csv')
    )

    if not os.path.exists(log_file_path):
        create_probe_request_log_file(log_file_path)

    with open(log_file_path, mode='a', newline='\n') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([
            now.hour, now.minute, now.second,
            src_mac, ssid
        ])


def create_probe_request_log_file(log_file_path):
    # type: (str) -> None
    """
    Creates a csv log file for the probe requests.

    Args:
        log_file_path (str): Path of the new csv log file.
    """

    os.makedirs(config['probe_request_log_directory'], exist_ok=True)

    header = [
        'hour', 'minute', 'second',
        'src_mac', 'ssid'
    ]

    with open(log_file_path, mode='w', newline='\n') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(header)


def create_error_log_file(exception):
    # type: (Exception) -> None
    """
    Creates an error log file with the given exception.

    Args:
        exception (Exception): Exception that was raised.
    """

    now = datetime.datetime.now()

    os.makedirs(config['error_log_directory'], exist_ok=True)

    error_file_path = os.path.join(
        config['error_log_directory'],
        now.strftime('%Y-%m-%d_%H-%M-%S.log')
    )

    with open(error_file_path, mode='w', newline='\n') as error_file:
        error_file.write(str(exception))


def main():

    try:
        interface_id = resolve_interface_id(config['interface_mac'])

        set_interface_state(interface_id, enabled=False)
        enable_monitor_mode(interface_id)
        set_interface_state(interface_id, enabled=True)

        gpio_thread = threading.Thread(target=check_gpio_pin_state)
        gpio_thread.start()

        scapy.sniff(
            iface=interface_id,
            prn=packet_handler,
            lfilter=lambda packet: packet.haslayer('Dot11ProbeReq'),
            stop_filter=lambda packet: not continue_sniff,
            store=False
        )

        gpio_thread.join()

    except Exception as e:
        create_error_log_file(e)

    finally:
        GPIO.cleanup()


if __name__ == '__main__':
    main()

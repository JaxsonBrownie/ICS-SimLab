#!/usr/bin/env python3

# FILE:     packet_based_generator.py
# PURPOSE:  Takes in a PCAP and builds a custom dataset with extracted features. The
#           dataset involves packet-based features.
# NOTE:     The features that this file have been drastically updated compared to the
#           original published paper.

import csv
import argparse
import pyshark
from scapy.all import rdpcap, IP, ARP, Ether, TCP, UDP
from scapy.contrib.modbus import ModbusADURequest, ModbusADUResponse
from datetime import datetime, timezone


# Function: flag_packet
# Purpose: Checks if a packet is malicious.
#   Malicious packets are either IP or ARP packets with source or
#   destination of 192.168.0.1
def flag_packet(packet):
    # initialise fields to search with
    hacker_ip = "192.168.0.1"
    is_attack = False
    
    # for IP layer packets
    if 'IP' in packet:
        ip_layer = packet['IP']

        # check if packets is to or from the hacker (192.168.0.1)
        if ip_layer.src == hacker_ip or ip_layer.dst == hacker_ip:
            is_attack = True
    
    # for ARP packets
    if 'ARP' in packet:
        arp_layer = packet['ARP']

        # check if it's an ARP request and the target IP matches
        if arp_layer.src.proto_ipv4 == hacker_ip:  # 1 is ARP request
            is_attack = True
    
    return is_attack


# Function: get_protocol
# Purpose: From a Scapy packet, returns the relevant protocol as a string
def get_protocol(packet):
    protcol = packet.highest_layer

    #if 'ARP' in packet:
    #    protcol = "ARP"
    #elif 'TCP' in packet:
        # check for ModbusTCP
    #    if ModbusADURequest in packet or ModbusADUResponse in packet:
    #        protcol = "ModbusTCP"
    #    else:
    #        protcol = "TCP"
    #elif 'UDP' in packet:
    #    protcol = "UDP"
    #elif 'IP' in packet:
    #    protcol = "IP"
    #elif Ether in packet:
    #    protcol = "Ethernet"
    #else:
    #    protcol = "Other"
    
    return protcol


# Function: reconstruct_modbus_data
# Purpose: Takes the lowest modbus Scapy layer and rebuilds the data field (only)
#   as a hex string
def reconstruct_modbus_data(modbus_layer):
    #modbus_layer = packet.getlayer(ModbusADURequest) or packet.getlayer(ModbusADUResponse)
    data_fields = {}

    # extract and reconstruct data field
    reconstructed_data = b""  # binary representation of the data field
    for field_desc in modbus_layer.fields_desc:
        field_name = field_desc.name

        if field_name in modbus_layer.fields:
            # get the value and binary representation of the field (excluding funcCode)
            if field_name != "funcCode":
                value = modbus_layer.fields[field_name]

                binary_data = field_desc.i2m(modbus_layer, value)  # Convert to binary
                data_fields[field_name] = value

                # reconstruct the data into bytes
                if isinstance(binary_data, list):
                    # convert each item in the list to bytes and concatenate
                    for item in binary_data:
                        if item == 0: # handle o item explicity for bit_length
                            reconstructed_data += b'\x00'
                        else:
                            reconstructed_data += item.to_bytes((item.bit_length() + 7) // 8, byteorder='big')
                elif isinstance(binary_data, int):
                    # convert int to bytes (big-endian format)
                    reconstructed_data += binary_data.to_bytes((binary_data.bit_length() + 7) // 8, byteorder='big')
                elif isinstance(binary_data, bytes):
                    # append raw bytes directly
                    reconstructed_data += binary_data
                else:
                    raise TypeError(f"Unexpected data type: {type(binary_data)}")

    return reconstructed_data.hex(), data_fields

# Function: get_attack_data
# Purpose: Uses the timestamp file to label each attack packet
def get_attack_data(packet, timestamp_file):
    # define attack categories
    attack_cat = {"0":"0", "1":"0", "2":"0", "3":"1", "4":"1", "5":"N/A", "6":"N/A",
               "7":"2", "8":"2", "9":"2", "10":"2", "11":"3", "12":"3"}

    # get and format packet time
    pkt_time = packet.sniff_time
    #pkt_time = datetime.fromtimestamp(float(packet.time), tz=timezone.utc)
    #pkt_time = pkt_time.strftime(f"%H:%M:%S.{int(packet.time % 1 * 1000):05d}")

    file = open(timestamp_file, 'r')
    lines = file.readlines()

    count = 0
    for line in lines:
        items = line.split(" : ")

        # get latest objective
        if "objective" in items[0]:
            obj = items[0]

        # convert the timestamp in the file to a datetime
        att_time = datetime.strptime(items[2].strip(), "%H:%M:%S.%f")

        # find the first items timestamp that is greater than the packets timestamp
        if att_time.time() > pkt_time.time():

            # get the attack 
            attack = items[0]
            
            # get corresponding attack category
            attack_num = ''.join(filter(str.isdigit, attack))
            if attack_num.isdigit():
                cat_num = attack_cat[attack_num]
            else:
                cat_num = "NOPE"

            # get objective number
            obj_num = ''.join(filter(str.isdigit, obj))
            return attack_num, cat_num, obj_num
        count += 1    
    return "N/A", "N/A", "N/A"


# Function: create_csv
# Purpose: Builds a CSV file from a parsed PCAP file, applying all required restrictions. 
def create_csv(packets, timestamp_file, output_file):
    with open(output_file, mode='w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)

        # write header row
        header = ["protocol",
                  "ether_src_mac", "ether_dst_mac", 
                  "ip_src", "ip_dst", "ip_len", "ip_flags_df", "ip_flags_mf", "ip_frag_offset", "ip_id", "ip_ttl", "ip_proto", "ip_checksum", 
                  "tcp_window_size", "tcp_ack", "tcp_seq", "tcp_len", "tcp_stream", "tcp_urgent_pointer", "tcp_flags", "tcp_analysis_ack_rtt", "tcp_analysis_push_bytes_sent", "tcp_analysis_bytes_in_flight",
                  "frame_time_relative", "frame_time_delta",
                  "modbus_length", "modbus_unit_id", "modbus_func_code", "modbus_data",
                  "attack_specific", "attack_category", "attack_obj", "attack_binary",]
        csv_writer.writerow(header)

        for pkt in packets:
            print(f"Processing packet number: {pkt.frame_info.number}")

            # initial instance data TODO: some might not be N/A
            ether_src_mac = "N/A"
            ether_dst_mac = "N/A"

            ip_src = "N/A"
            ip_dst = "N/A"
            ip_len = "N/A"
            ip_flags_df = "N/A"
            ip_flags_mf = "N/A"
            ip_frag_offset = "N/A"
            ip_id = "N/A"
            ip_ttl = "N/A"
            ip_proto = "N/A"
            ip_checksum = "N/A"

            tcp_window_size = "N/A"
            tcp_ack = "N/A"
            tcp_seq = "N/A"
            tcp_len = "N/A"
            tcp_stream = "N/A"
            tcp_urgent_pointer = "N/A"
            tcp_flags = "N/A"
            tcp_analysis_ack_rtt = "N/A"
            tcp_analysis_push_bytes_sent = "N/A"
            tcp_analysis_bytes_in_flight = "N/A"

            frame_time_relative = "N/A"
            frame_time_delta = "N/A"

            modbus_length = "N/A"
            modbus_unit_id = "N/A"
            modbus_func_code = "N/A"
            modbus_data = "N/A"

            attack_specific = "N/A"
            attack_category = "N/A"
            attack_obj = "N/A"
            attack_binary = 0
        
            # remove UDP packets (unwanted) TODO: could probably make much easier
            protocol = get_protocol(pkt)

            # ignore UDP TODO: check why this is the case
            #if protocol == "UDP":
            #    continue

            # data link information
            if "ETH" in pkt:
                eth_layer = pkt.eth
                ether_src_mac = eth_layer.src
                ether_dst_mac = eth_layer.dst

            # IP information
            if "IP" in pkt:
                ip_layer = pkt.ip

                ip_src = ip_layer.src
                ip_dst = ip_layer.dst
                ip_len = ip_layer.len,
                ip_flags_df = ip_layer.flags_tree.df
                ip_flags_mf = ip_layer.flags_tree.mf
                ip_frag_offset = ip_layer.frag_offset
                ip_id = ip_layer.id
                ip_ttl = ip_layer.ttl
                ip_proto = ip_layer.proto
                ip_checksum = ip_layer.checksum

            # TCP information
            if "TCP" in pkt:
                tcp_layer = pkt.tcp
                #print(tcp_layer)
                
                tcp_window_size = tcp_layer.window_size_value
                tcp_ack = tcp_layer.ack
                tcp_seq = tcp_layer.seq
                tcp_len = tcp_layer.len
                tcp_stream = tcp_layer.stream
                tcp_urgent_pointer = tcp_layer.urgent_pointer
                tcp_flags = tcp_layer.flags

                if hasattr(tcp_layer, "analysis"):
                    tcp_analysis_ack_rtt = getattr(tcp_layer.analysis, "ack_rtt", "N/A")
                    tcp_analysis_push_bytes_sent = getattr(tcp_layer.analysis, "push_bytes_sent", "N/A")
                    tcp_analysis_bytes_in_flight = getattr(tcp_layer.analysis, "bytes_in_flight", "N/A")
                    #tcp_reassembled_length = getattr(tcp_layer, 'reassembled_length', "N/A")

                    #if 'reassembled' in tcp_layer.field_names:
                    #    print("Reassembled length found!")
                    #    reassembled_len = tcp_layer.get_field_value('reassembled.length')
                    #    print("Length:", reassembled_len)
                
                #tcp_time_relative = getattr(tcp_layer, "time_relative", "N/A")
                #if "time_relative" in tcp_layer.field_names:
                #    print("FOUND")
                #tcp_time_delta = tcp_layer.time_delta

            # frame information            
            frame_time_relative = pkt.frame_info.time_relative
            frame_time_delta = pkt.frame_info.time_delta

            # TODO: extract modbus information
            # modbus information
            if "MODBUS" in pkt:
                print(pkt.modbus)
                #modbus_adu_layer = pkt.getlayer(3)
                #modbus_layer = pkt.getlayer(4)

                #length = modbus_adu_layer.len if modbus_adu_layer != None else "N/A"
                #unit_id = modbus_adu_layer.unitId if modbus_adu_layer != None else "N/A"
                #func_code = f'{modbus_layer.funcCode:x}' if modbus_layer != None else "N/A"

                # rebuild data field
                #if modbus_layer != None:
                #    data, _ = reconstruct_modbus_data(modbus_layer)

            # attack specific information
            if flag_packet(pkt):
                attack_binary = 1

                # read the timestamps file and determine which specfic/obj/category attack it is
                attack_specific, attack_category, attack_obj = get_attack_data(pkt, timestamp_file)

            # write to csv
            csv_writer.writerow([protocol,
                                 ether_src_mac, ether_dst_mac,
                                 ip_src, ip_dst, ip_len[0], ip_flags_df, ip_flags_mf, ip_frag_offset, ip_id, ip_ttl, ip_proto, ip_checksum,
                                 tcp_window_size, tcp_ack, tcp_seq, tcp_len, tcp_stream, tcp_urgent_pointer, tcp_flags, 
                                 tcp_analysis_ack_rtt, tcp_analysis_push_bytes_sent, tcp_analysis_bytes_in_flight,
                                 frame_time_relative, frame_time_delta,
                                 modbus_length, modbus_unit_id, modbus_func_code, modbus_data,
                                 attack_specific, attack_category, attack_obj, attack_binary])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--pcap", required=True)
    parser.add_argument("-t", "--timestamp", required=True)
    parser.add_argument("-o", "--output", required=True)

    args = parser.parse_args()
    pcap_file = args.pcap
    timestamp_file = args.timestamp
    output_file = args.output

    print(f"PCAP file: {pcap_file}")
    print(f"TIMESTAMP file: {timestamp_file}")
    print(f"DATASET (OUTPUT) file: {output_file}")
    print()
    print(f"Creating dataset from these files")

    # read pcap
    print(f"<1/2> Reading PCAP file: {pcap_file}")
    #packets = rdpcap(pcap_file)
    packets = pyshark.FileCapture(pcap_file, use_json=True)

    # create dataset
    print("<2/2> Creating CSV dataset")
    create_csv(packets, timestamp_file, output_file)

    print("Finished!")
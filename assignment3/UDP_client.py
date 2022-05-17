# CS 3357 Assignment 4
# Sonia Spence (250 970 384)
# 8th December 2021


import socket
import os
import signal
import sys
import sys
import argparse
from urllib.parse import urlparse
import selectors
import struct
import hashlib

# Define a constant for our buffer size, UDP IP, and maximum string size
BUFFER_SIZE = 1024
UDP_IP = "127.0.0.1"
MAX_STRING_SIZE = 256

# Socket for sending messages.
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# User name for tagging sent messages.
user = ''


# Signal handler for graceful exiting.  Let the server know when we're gone.
def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    message = f'DISCONNECT {user} CHAT/1.0\n'
    # Would have included message to server to shut down on that end
    sys.exit(0)


# Simple function for setting up a prompt for the user.
def do_prompt(skip_line=False):
    if skip_line:
        print("")
    print("> ", end='', flush=True)


# Function to create packet and send it using RDT 3.0
def send_message(ack, message, sequence_number, port):
    # Create checksum
    data = message.encode()
    size = len(data)
    ack = 1
    packet_tuple = (ack, sequence_number, size, data)
    packet_structure = struct.Struct(f'I I I {MAX_STRING_SIZE}s')
    packed_data = packet_structure.pack(*packet_tuple)
    checksum = bytes(hashlib.md5(packed_data).hexdigest(), encoding="UTF-8")
    global client_port

    # Build UDP packet
    packet_tuple = (ack, sequence_number, size, data, checksum)
    UDP_packet_structure = struct.Struct(f'I I I {MAX_STRING_SIZE}s 32s')
    UDP_packet = UDP_packet_structure.pack(*packet_tuple)

    # Send packet to server using RDT 3.0
    while True:
        try:
            client_socket.sendto(UDP_packet, (UDP_IP, port))
            unpacker = struct.Struct(f'I I I {MAX_STRING_SIZE}s 32s')
            # Set timeout
            client_socket.settimeout(1.00)
            data, addr = client_socket.recvfrom(1024)
            UDP_packet_a = unpacker.unpack(data)
            # If ACKed and checksums match then exit loop
            if(UDP_packet_a[0] == 1) & (UDP_packet_a[4] == checksum):
                break
            # If checksum does not match keep looping
            if UDP_packet_a[4] != checksum:
                continue
        # If there is a timeout keep looping
        except socket.timeout:
            continue


# Function to handle input from user.
def handle_keyboard_input(file, mask):
    line = sys.stdin.readline()
    message = f'@{user}: {line}'
    send_message(message)
    do_prompt()


# Our main function.
def main():
    global user
    global client_socket

    # Register our signal handler for shutting down.
    signal.signal(signal.SIGINT, signal_handler)

    # Check command line arguments to retrieve a URL.
    parser = argparse.ArgumentParser()
    parser.add_argument("user", help="user name for this user on the chat service")
    parser.add_argument("server", help="URL indicating server location in form of chat://host:port")
    parser.add_argument('-f', '--follow', nargs=1, default=[], help="comma separated list of users/topics to follow")
    args = parser.parse_args()

    # Check the URL passed in and make sure it's valid.  If so, keep track of
    # things for later.
    try:
        server_address = urlparse(args.server)
        if (server_address.scheme != 'chat') or (server_address.port is None) or (server_address.hostname is None):
            raise ValueError
        host = server_address.hostname
        port = server_address.port
    except ValueError:
        print('Error:  Invalid server.  Enter a URL of the form:  chat://host:port')
        sys.exit(1)
    user = args.user
    follow = args.follow

    # print('Sending message to server ...')
    message = f'REGISTER {user} CHAT/1.0\n'

    # Packet initializations
    sequence_number = 0
    data = message.encode()
    size = len(data)
    ack = 0

    # Create checksum
    packet_tuple = (ack, sequence_number, size, data)
    packet_structure = struct.Struct(f'I I I {MAX_STRING_SIZE}s')
    packed_data = packet_structure.pack(*packet_tuple)
    checksum = bytes(hashlib.md5(packed_data).hexdigest(), encoding="UTF-8")

    # Create packet
    packet_tuple = (ack, sequence_number, size, data, checksum)
    UDP_packet_structure = struct.Struct(f'I I I {MAX_STRING_SIZE}s 32s')
    UDP_packet = UDP_packet_structure.pack(*packet_tuple)

    addr, client_port = client_socket.getsockname()
    client_socket.bind((UDP_IP, client_port))
    # Send packets over UDP
    while True:
        # RDT 3.0 implementation to make sure checksum matches and ACKed
        try:
            client_socket.sendto(UDP_packet, (UDP_IP, port))
            unpacker = struct.Struct(f'I I I {MAX_STRING_SIZE}s 32s')
            # Set timeout
            client_socket.settimeout(1.00)
            data, addr = client_socket.recvfrom(1024)
            UDP_packet_a = unpacker.unpack(data)
            # If ACKed and checksums match exit loop
            if(UDP_packet_a[0] == 1) & (UDP_packet_a[4] == checksum):
                print('Registration successful. Ready for messaging!')
                break
            # If checksums do not match keep looping
            if UDP_packet_a[4] != checksum:
                continue
        # If socket times out keep looping
        except socket.timeout:
            continue
    do_prompt()

    # While loop to keep handling user input
    while True:
        a = input()
        send_message(1, a, sequence_number, port)


if __name__ == '__main__':
    main()

# CS 3357 Assignment 4
# Sonia Spence (250 970 384)
# 8th December 2021

import socket
import os
import datetime
import signal
import sys
import selectors
from string import punctuation
import struct
import hashlib

# Constant for our buffer size, UDP IP, and maximum string size
BUFFER_SIZE = 1024
UDP_IP = "127.0.0.1"
MAX_STRING_SIZE = 256

# User name for tagging received messages to display on server.
user = ''
projected_sequence_num = 0


# Signal handler for graceful exiting.  We let clients know in the process so they can disconnect too.
def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    message = 'DISCONNECT CHAT/1.0\n'
    # send disconnect message to client didnt get to implement
    sys.exit(0)


# Removed list, follow, and remove client because there is only one client at a time so these functions don't do anything

# Function to check if the client is new and print the appropriate messages if the registration message is incorrect
def check_new_client(sock, message):
    message_parts = message.split()

    # Check format of request.
    if ((len(message_parts) != 3) or (message_parts[0] != 'REGISTER') or (message_parts[2] != 'CHAT/1.0')):
        print('Error:  Invalid registration message.')
        print('Received: ' + message)
        print('Connection closing ...')

    # If request is properly formatted and user not already listed, go ahead with registration.
    else:
        print('Accepted connection from client')
        global user
        user = message_parts[1]
        print(f'Connection to client established, waiting to receive messages from user \'{user}\'...')



# Function to read messages from clients.

def read_message(sock, message):
    # Does this indicate a closed connection?
    if message == '':
        print('Closing connection')
        # send message to client indicating closed connection has not been implemented

    # Receive the message.
    else:
        words = message.split(' ')
        words = message.split(' ')

        if words[0] == 'REGISTER':
            check_new_client(sock, message)

        else:
            print(f'Received message from user {user}:  ' + message)


# Function to create ACKed package to send back to client
def ack_package(ack, UDP_packet, checksum):
    send_back = (ack, projected_sequence_num, UDP_packet[2], UDP_packet[3], checksum)
    UDP_packet_info = struct.Struct(f'I I I {MAX_STRING_SIZE}s 32s')
    UDP_packet = UDP_packet_info.pack(*send_back)
    return UDP_packet

# Function to manage the sequence numbers
def manage_sequence_nums():
    global projected_sequence_num
    if projected_sequence_num == 0:
        projected_sequence_num = 1
    else:
        projected_sequence_num = 0


# Our main function.
def main():
    # Register our signal handler for shutting down.
    signal.signal(signal.SIGINT, signal_handler)

    # Create the socket.
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('', 0))
    print('Will wait for client connections at port ' + str(server_socket.getsockname()[1]))

    # Next, we loop forever waiting for packets to arrive from clients.
    while True:
        # Unpack the packet from the client
        received_packet, addr = server_socket.recvfrom(1024)
        unpacker = struct.Struct(f'I I I {MAX_STRING_SIZE}s 32s')
        UDP_packet = unpacker.unpack(received_packet)

        # Extract out data that was received from the packet. Put into variables
        received_ack = UDP_packet[0]
        received_sequence = UDP_packet[1]
        received_size = UDP_packet[2]
        received_data = UDP_packet[3]
        received_checksum = UDP_packet[4]

        # Compute checksum
        values = (received_ack, received_sequence, received_size, received_data)
        packer = struct.Struct(f'I I I {MAX_STRING_SIZE}s')
        packed_data = packer.pack(*values)
        computed_checksum = bytes(hashlib.md5(packed_data).hexdigest(), encoding="UTF-8")

        # Compare checksums to see if there is any loss or corruption
        if received_checksum == computed_checksum:
            received_text = received_data[:received_size].decode()
            read_message(server_socket, received_text)
            # ACK packet and send back to client
            manage_sequence_nums()
            package_to_send = ack_package(1, UDP_packet, computed_checksum)
            conn, port = addr
            server_socket.sendto(package_to_send, (UDP_IP, port))
        else:
            print('Packet has been received and is corrupt and discarded')


if __name__ == '__main__':
    main()

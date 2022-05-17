# CS 3357 Assignment 2
# Sonia Spence (250 970 384)
# 20th October 2021
import socket
import os
import sys
import argparse
from urllib.parse import urlparse
import selectors
import signal


# function to run client
def run():
    sel = selectors.DefaultSelector  # create selector
    parser = argparse.ArgumentParser()  # parse arguments
    parser.add_argument("username")
    parser.add_argument("url", help="URL to fetch with an HTTP GET request")
    args = parser.parse_args()
    try:
        parsed_username = args.username  # save username from args
        parsed_url = urlparse(args.url)  # parse url

        if (parsed_username is None) or (parsed_url.scheme != 'chat') or (parsed_url.port == '') or (
                parsed_url.hostname is None):  # check if valid
            raise ValueError

        username = parsed_username  # put username from args in variable
        host = parsed_url.hostname  # put host name from url in variable
        port = parsed_url.port  # put port number from url in variable

    except ValueError:
        print('Error:  Invalid URL.  Enter a URL of the form:  username chat://host:port')  # if the URL is not in the right format print error message
        sys.exit(1)

    start_connections(host, port, username)  # use args to start a connection to server

    while True:  # loop through to keep checking for new messages from port
        accept_message()


# exception to handle control c exit
def signal_handler(sig, frame):
    print('CInterupt received shutting down...')
    sys.exit(0)  # shut down client


# function to deal with messages
def accept_message(key, mask, username):
    client_socket = key.fileobj
    data = key.data

    if mask & selectors.EVENT_READ:  # if in read mask
        recv_data = client_socket.recv(1024)  # receive message

        if recv_data:  # if there is a message
            message = recv_data.message.decode()
            print('> ', message)  # print message

    if mask & selectors.EVENT_WRITE:  # if there is a write mask
        if input() != '':  # if there is input from user
            message = input()
            data = (username, message)
            message = ('@', username, ': ', message)
            client_socket.send(data.encode)  # send input from user as message in socket


# function to add make connection to server
def start_connections(host, port, username):
    print('Connecting to Server...')
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        client_socket.setblocking(False)
        address = (host, port)
        client_socket.connect_ex(address)
        message = ''
        data = (username, message)  # set up tuple of username and messages
        events = selectors.EVENT_READ | selectors.EVENT_WRITE  # read and write masks

    except ConnectionRefusedError:
        print('Error:  That host or port is not accepting connections.') # if the connection is not successful print error message
        sys.exit(1)  # shut down client

    print('Registration succesful. Ready for messaging!')


def main():
    run()


if __name__ == '__main__':
    main()

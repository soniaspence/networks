# CS 3357 Assignment 2
# Sonia Spence (250 970 384)
# 20th October 2021
import socket
import sys
import signal
import selectors

sel = selectors.DefaultSelector()
message = ''


# function to run the server
def run():
    signal.signal(signal.SIGINT, signal_handler)
    socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_server.bind(('', 0))
    print('Will wait for client connections at port ', str(socket_server.getsockname()[1]))
    socket_server.listen()
    print('Waiting for incoming client connections ...')
    socket_server.setblocking(False)

    sel.register(socket_server, selectors.EVENT_READ, data=None)  # register selector

    while True:  # while loop through program checks if need a new client or accept a message
        for key, mask in sel.select(timeout=None):
            if key.data is None:
                accept(key.fileobj)
            else:
                accept_message(key, mask)


# function that checks if there is a message
def accept_message(key, mask):
    socket_server = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:  # if the mask is set to read
        data = socket_server.recv(1024)
        if data:
            username = data.username
            message = data.message
            print('Received message from user', username, ': ', message)  # print message to user


# exception to handle control c exit
def signal_handler(sig, frame):
    sys.exit(0)


# function to connect to client
def accept(socket_server):
    conn, address = socket_server.accept()  # accept client connection
    print('Accepted connection from client address: (', address, ')')
    conn.setblocking(False)
    username = ''
    data = (username, message)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    if conn.recv:  # if a message is received
        sel.register(socket_server, events, data=data)
        username = data.username.decode()
        print("Connection to client established, waiting to receive messages from user'", username, "'...")
    else:
        # didnt get here but would have been sending an error message to client to initiate disconnect
        """print('Received message from user ', username, ': DISCONNECT ', username, 'CHAT/1.0')
        print('Disconnecting user ', username)
        sel.unregister(conn) # unregister if there is n
        signal_handler()"""
        # this block above would have printed appropriate message if a client disconnected from server


def main():
    run()


if __name__ == '__main__':
    main()

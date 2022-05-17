# CS 3357 Assignment 2
# Sonia Spence (250 970 384)
# 9th November 2021


import socket
import os
import signal
import sys
import selectors
import string

# Selector for helping us select incoming data and connections from multiple sources.

sel = selectors.DefaultSelector()

# Client list for mapping connected clients to their connections.

client_list = []
client_names = []
follow_list = []
follow_user = []


# Signal handler for graceful exiting.  We let clients know in the process so they can disconnect too.

def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    message = 'DISCONNECT CHAT/1.0\n'
    for reg in client_list:
        reg[1].send(message.encode())
    sys.exit(0)


# Read a single line (ending with \n) from a socket and return it.
# We will strip out the \r and the \n in the process.

def get_line_from_socket(sock):
    done = False
    line = ''
    while (not done):
        char = sock.recv(1).decode()
        if (char == '\r'):
            pass
        elif (char == '\n'):
            done = True
        else:
            line = line + char
    return line


# Search the client list for a particular user.

def client_search(user):
    for reg in client_list:
        if reg[0] == user:
            return reg[1]
    return None


# Search the client list for a particular user by their socket.

def client_search_by_socket(sock):
    for reg in client_list:
        if reg[1] == sock:
            return reg[0]
    return None


# Add a user to the client list.

def client_add(user, conn):
    registration = (user, conn)
    client_names.append(user)
    client_list.append(registration)
    follow_user.append(user)
    follow_list.append("@" + user)


# Remove a client when disconnected.

def client_remove(user):
    for reg in client_list:
        if reg[0] == user:
            client_list.remove(reg)
            break


# Function to read commands from clients and send appropriate data

def handle_command(words, user):
    # List the users
    if words[1] == "!list":
        flag = 0
        for x in range(len(follow_user)):
            if flag == 0:
                message = follow_user[x]
                flag = 1

            # Make sure no duplicate users in list
            else:
                if follow_user[x] not in message:
                    message = message + ', ' + follow_user[x]

        message = f'{message}\n'
        client_search(user).send(message.encode())

    # Follow a term
    if words[1] == "!follow":
        if len(words) > 2 and words[2] not in follow_list:
            follow_list.append(words[2])
            follow_user.append(user)
            message = "Now following " + words[2]

        # Make sure there is a term to unfollow
        else:
            message = "Error: invalid command"
        message = f'{message}\n'
        client_search(user).send(message.encode())

    # List the terms the user follows
    if words[1] == "!follow?":
        message = ''
        flag = 0
        for x in range(len(follow_user)):
            if follow_user[x] == user:
                if flag == 0:
                    message = follow_list[x]
                    flag = 1
                else:
                    message = message + ', ' + follow_list[x]
        message = f'{message}\n'
        client_search(user).send(message.encode())

    if words[1] == '!unfollow':
        flag = 0
        if len(words) > 2:
            for x in range(len(follow_user)):
                if follow_user[x] == user:
                    if follow_list[x] == words[2]:
                        del follow_user[x]
                        del follow_list[x]
                        message = "No longer following " + words[2]
                        flag = 1
        if flag == 0:
            message = "Error: invalid command"

        message = f'{message}\n'
        client_search(user).send(message.encode())

    # Disconnect the user
    if words[1] == '!exit':
        print('Disconnecting user ' + user)
        sock = client_search(user)
        message = 'DISCONNECT CHAT/1.0\n'
        sock.send(message.encode())
        client_remove(user)
        sel.unregister(sock)
        sock.close()

    if words[1] == '!attach':
        handle_file(words, user)


def handle_file(words, user):
    return
    # Did not get to this part but would have created a while loop to check who to send the message
    # to and send it to the user requesting the transfer if there was no recipient


# Function that checks the following lists every time someone sends a message

def check_follow(user, words, message):
    for x in range(len(follow_list)):
        for y in range(len(words)):
            target = follow_list[x].translate(string.punctuation)

            # Is there a match?

            if words[y].startswith(target):
                message = f'{message}\n'
                user_receive = client_search(follow_user[x])

                # Is the message from a different user than the user on the follow list?

                if follow_user[x] != user:
                    user_receive.send(message.encode())


# Function to read messages from client

def read_message(sock, mask):
    message = get_line_from_socket(sock)

    # Does this indicate a closed connection?

    if message == '':
        print('Closing connection')
        sel.unregister(sock)
        sock.close()

    # Receive the message.

    else:
        user = client_search_by_socket(sock)
        words = message.split(' ')

        try:
            if words[1][0] == "!":
                handle_command(words, user)
                # print(words[1][0])
            else:
                check_follow(user, words, message)
                print(f'Received message from user {user}:  ' + message)
            # Check for client disconnections.

            if words[0] == 'DISCONNECT':
                print('Disconnecting user ' + user)
                client_remove(user)
                sel.unregister(sock)
                sock.close()

            # Send message to all users.  Send at most only once, and don't send to yourself.
            # Need to re-add stripped newlines here.

            if "@all" in words:
                for reg in client_list:
                    if reg[0] == user:
                        continue
                    client_sock = reg[1]
                    forwarded_message = f'{message}\n'
                    client_sock.send(forwarded_message.encode())
        except IndexError:
            print("Error: Invalid input from user")

# Function to accept and set up clients.

def accept_client(sock, mask):
    conn, addr = sock.accept()
    print('Accepted connection from client address:', addr)
    message = get_line_from_socket(conn)
    message_parts = message.split()

    # Check format of request.

    if ((len(message_parts) != 3) or (message_parts[0] != 'REGISTER') or (message_parts[2] != 'CHAT/1.0') or (
            message_parts[1] == "all")):
        print('Error:  Invalid registration message.')
        print('Received: ' + message)
        print('Connection closing ...')
        response = '400 Invalid registration\n'
        conn.send(response.encode())
        conn.close()

    # If request is properly formatted and user not already listed, go ahead with registration.

    else:
        user = message_parts[1]

        if client_search(user) is None:
            client_add(user, conn)
            print(f'Connection to client established, waiting to receive messages from user \'{user}\'...')
            response = '200 Registration succesful\n'
            conn.send(response.encode())
            conn.setblocking(False)
            sel.register(conn, selectors.EVENT_READ, read_message)

        # If user already in list, return a registration error.

        else:
            print('Error:  Client already registered.')
            print('Connection closing ...')
            response = '401 Client already registered\n'
            conn.send(response.encode())
            conn.close()


# Our main function.

def main():
    # Register our signal handler for shutting down.

    signal.signal(signal.SIGINT, signal_handler)

    # Create the socket.  We will ask this to work on any interface and to pick
    # a free port at random.  We'll print this out for clients to use.

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', 0))
    print('Will wait for client connections at port ' + str(server_socket.getsockname()[1]))
    server_socket.listen(100)
    server_socket.setblocking(False)
    sel.register(server_socket, selectors.EVENT_READ, accept_client)
    print('Waiting for incoming client connections ...')

    # Keep the server running forever, waiting for connections or messages.

    while (True):
        events = sel.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)


if __name__ == '__main__':
    main()

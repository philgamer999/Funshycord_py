import socket
import threading
import json

clients = {}
addresses = {}

HOST = '127.0.0.1'
PORT = 12345
BUFFER_SIZE = 1024
ADDRESS = (HOST, PORT)

EXIT_CODE = "/bye"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDRESS)

def handle_client(client_socket):
    name = client_socket.recv(BUFFER_SIZE).decode("utf8")
    welcome = f'Welcome {name}! Type {EXIT_CODE} to exit.'
    client_socket.send(bytes(welcome, "utf8"))
    msg = f'{name} has joined the chat!'
    broadcast(msg, clients.keys())
    clients[client_socket] = name

    while True:
        msg = client_socket.recv(BUFFER_SIZE).decode("utf8")
        if msg != f"{EXIT_CODE}":
            try:
                data = json.loads(msg)
                message = data['message']
                receivers = data['receivers']
                receiver_sockets = [sock for sock, client_name in clients.items() if client_name in receivers]
                broadcast(message, receiver_sockets, name + ": ")
            except (json.JSONDecodeError, KeyError):
                client_socket.send(bytes("Invalid message format.", "utf8"))
        else:
            client_socket.send(bytes(f"{EXIT_CODE}", "utf8"))
            client_socket.close()
            del clients[client_socket]
            broadcast(f'{name} has left the chat.', clients.keys())
            break

def broadcast(msg, receivers, prefix=""):
    for sock in receivers:
        sock.send(bytes(prefix + msg, "utf8"))
    print(f"{prefix}{msg}")    

def accept_incoming_connections():
    while True:
        client_socket, client_address = server.accept()
        print(f'{client_address} has connected.')
        client_socket.send(bytes("Enter your name: ", "utf8"))
        addresses[client_socket] = client_address
        threading.Thread(target=handle_client, args=(client_socket,)).start()

if __name__ == "__main__":
    server.listen(5)
    print("Waiting for connection...")
    ACCEPT_THREAD = threading.Thread(target=accept_incoming_connections)
    ACCEPT_THREAD.start()
    ACCEPT_THREAD.join()
    server.close()
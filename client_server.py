import os
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
import json

# Server code
clients = {}
addresses = {}

HOST = '127.0.0.1'
PORT = 12345
BUFFER_SIZE = 1024
ADDRESS = (HOST, PORT)

EXIT_CODE = "/bye"
SERVER_PING = "<PING>"

#Path
FILE_PATH = f"{os.path.dirname(__file__)}"
DATA_PATH = f"{FILE_PATH}/data"
COLOR_SCHEME_FILE = f"{DATA_PATH}/color_scheme.json"
if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH)

COLOR_SCHEME = {
    "WINDOW": {
        "bg": "#0f0f0f",
        "fg": "#646464",
        "bd": 2,
        "relief": "solid"
    },
    "BUTTON": {
        "fg": "#646464",
        "bg": "#141414",
        "bd": 2,
        "relief": "solid"
    },
    "LABEL": {
        "fg": "#646464",
        "bg": "#0f0f0f",
        "bd": 2,
        "relief": "solid"
    },
    "TEXT": {
        "fg": "#646464",
        "bg": "#141414",
        "bd": 2,
        "relief": "solid"
    },
    "SCROLLED_TEXT": {
        "state": "disabled",
        "fg": "#646464",
        "bg": "#141414",
        "bd": 2,
        "relief": "solid"
    },
    "ENTRY": {
        "fg": "#646464",
        "bg": "#141414",
        "bd": 2,
        "relief": "solid"
    }
}

client = None
server = None

def log(message):
    print(message)

class ChatServer:
    def __init__(self, host='127.0.0.1', port=12345):
        self.server_window = tk.Tk()
        self.server_window.protocol("WM_DELETE_WINDOW", self.close_server)
        self.server_window.title("Server Console")
        self.server_window.geometry("800x600+10+10")
        self.server_window.configure(bg=COLOR_SCHEME["WINDOW"]["bg"])

        self.server_console = scrolledtext.ScrolledText(self.server_window, state=COLOR_SCHEME["SCROLLED_TEXT"]["state"], bg=COLOR_SCHEME["SCROLLED_TEXT"]["bg"], fg=COLOR_SCHEME["SCROLLED_TEXT"]["fg"], bd=COLOR_SCHEME["SCROLLED_TEXT"]["bd"], relief=COLOR_SCHEME["SCROLLED_TEXT"]["relief"])
        self.server_console.pack()

        close_button = tk.Button(self.server_window, text="Close Server", command=self.close_server, fg=COLOR_SCHEME["BUTTON"]["fg"], bg=COLOR_SCHEME["BUTTON"]["bg"], bd=COLOR_SCHEME["BUTTON"]["bd"], relief=COLOR_SCHEME["BUTTON"]["relief"])
        close_button.pack()

        self.clients = {}
        self.addresses = {}
        self.HOST = host
        self.PORT = port
        self.BUFFER_SIZE = 1024
        self.ADDRESS = (self.HOST, self.PORT)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.stop_event = threading.Event()
        log(f"Server started: {self.HOST}:{self.PORT}({self.BUFFER_SIZE})")

        self.start_server()
        self.server_window.mainloop()

    def handle_client(self, client_socket):
        name = client_socket.recv(self.BUFFER_SIZE).decode("utf8")
        welcome = f'Welcome {name}! Type {EXIT_CODE} to exit.'
        client_socket.send(bytes(welcome, "utf8"))
        msg = f'{name} has joined the chat!'
        self.broadcast(msg, self.clients.keys())
        self.clients[client_socket] = name

        while not self.stop_event.is_set():
            try:
                msg = client_socket.recv(self.BUFFER_SIZE).decode("utf8")
                data = json.loads(msg)
                message = data['message']
                receivers = data['receivers']
                if message == f"{EXIT_CODE}":
                    client_socket.send(bytes(f"{EXIT_CODE}", "utf8"))
                    client_socket.close()
                    del self.clients[client_socket]
                    self.broadcast(f'{name} has left the chat.', self.clients.keys())
                    break
                elif message == SERVER_PING:
                    client_socket.send(bytes(SERVER_PING, "utf8"))
                else:
                    receiver_sockets = [sock for sock, client_name in self.clients.items() if client_name in receivers]
                    self.broadcast(message, receiver_sockets, name + ": ")
            except (json.JSONDecodeError, KeyError):
                client_socket.send(bytes("Invalid message format.", "utf8"))
            except:
                break

    def server_console(self, message):
        log(f"{message}")
        self.server_console.config(state='normal')
        self.server_console.insert(tk.END, message + '\n')
        self.server_console.config(state='disabled')

    def broadcast(self, msg, receivers, prefix=""):
        for sock in receivers:
            sock.send(bytes(prefix + msg, "utf8"))
        self.server_console(f"{prefix}{msg}")

    def accept_incoming_connections(self):
        while not self.stop_event.is_set():
            try:
                client_socket, client_address = self.server.accept()
                self.server_console(f'{client_address} has connected.')
                client_socket.send(bytes("Enter your name: ", "utf8"))
                self.addresses[client_socket] = client_address
                threading.Thread(target=self.handle_client, args=(client_socket,)).start()
            except:
                break

    def start_server(self):
        self.server.bind(self.ADDRESS)
        self.server.listen(5)
        self.server_console("Waiting for connection...")
        self.accept_thread = threading.Thread(target=self.accept_incoming_connections)
        self.accept_thread.start()

    def close_server(self, shutdown=False):
        log("Shutting down Server...")

        # Signal threads to stop    
        self.stop_event.set()

        # Close the server socket
        if self.server:
            self.server.close()
            self.server = None

        # End all client connections
        for client_socket in list(self.clients.keys()):
            try:
                client_socket.send(bytes(EXIT_CODE, "utf8"))
                client_socket.close()
            except:
                pass  # Ignore if the socket is already closed

        # Wait for the accept thread to finish
        if self.accept_thread:
            self.accept_thread.join(timeout=2)
            self.accept_thread = None

        # Close the server window
        if self.server_window:
            self.server_window.destroy()
            self.server_window = None

        log("Server stopped!")

        # Reopen the start window after server closes
        if not shutdown:
            main()

class ChatClient:
    def __init__(self, username):
        self.client_window = tk.Tk()
        self.client_window.protocol("WM_DELETE_WINDOW", self.disconnect)
        self.client_window.title("Chat Client")
        #self.root.geometry("400x400+10+10")
        self.client_window.configure(bg=COLOR_SCHEME["WINDOW"]["bg"])

        self.client_socket = None
        self.stop_event = threading.Event()

        self.username = username

        self.receivers_label = tk.Label(self.client_window, text="Receivers (comma separated):", fg=COLOR_SCHEME["LABEL"]["fg"], bg=COLOR_SCHEME["LABEL"]["bg"], bd=COLOR_SCHEME["LABEL"]["bd"], relief=COLOR_SCHEME["LABEL"]["relief"])
        self.receivers_label.pack()
        self.receivers_entry = tk.Entry(self.client_window, fg=COLOR_SCHEME["ENTRY"]["fg"], bg=COLOR_SCHEME["ENTRY"]["bg"], bd=COLOR_SCHEME["ENTRY"]["bd"], relief=COLOR_SCHEME["ENTRY"]["relief"])
        self.receivers_entry.pack()

        self.message_label = tk.Label(self.client_window, text="Message:", fg=COLOR_SCHEME["LABEL"]["fg"], bg=COLOR_SCHEME["LABEL"]["bg"], bd=COLOR_SCHEME["LABEL"]["bd"], relief=COLOR_SCHEME["LABEL"]["relief"])
        self.message_label.pack()
        self.message_entry = tk.Entry(self.client_window, fg=COLOR_SCHEME["ENTRY"]["fg"], bg=COLOR_SCHEME["ENTRY"]["bg"], bd=COLOR_SCHEME["ENTRY"]["bd"], relief=COLOR_SCHEME["ENTRY"]["relief"])
        self.message_entry.pack()

        self.send_button = tk.Button(self.client_window, text="Send", command=self.send_message, fg=COLOR_SCHEME["BUTTON"]["fg"], bg=COLOR_SCHEME["BUTTON"]["bg"], bd=COLOR_SCHEME["BUTTON"]["bd"], relief=COLOR_SCHEME["BUTTON"]["relief"])
        self.send_button.pack()

        self.disconnect_button = tk.Button(self.client_window, text="Disconnect", command=self.disconnect, fg=COLOR_SCHEME["BUTTON"]["fg"], bg=COLOR_SCHEME["BUTTON"]["bg"], bd=COLOR_SCHEME["BUTTON"]["bd"], relief=COLOR_SCHEME["BUTTON"]["relief"])
        self.disconnect_button.pack()

        self.chat_area = scrolledtext.ScrolledText(self.client_window, state=COLOR_SCHEME["SCROLLED_TEXT"]["state"], bg=COLOR_SCHEME["SCROLLED_TEXT"]["bg"], fg=COLOR_SCHEME["SCROLLED_TEXT"]["fg"], bd=COLOR_SCHEME["SCROLLED_TEXT"]["bd"], relief=COLOR_SCHEME["SCROLLED_TEXT"]["relief"])
        self.chat_area.pack()

        self.connect_to_server()
        self.client_window.mainloop()

    def connect_to_server(self):
        host = '127.0.0.1'  # Server IP address
        port = 12345        # Server port

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((host, port))
            self.stop_event.clear()
            self.client_socket.send(self.username.encode('utf-8'))
            threading.Thread(target=self.receive_messages, daemon=True).start()
        except ConnectionRefusedError:
            self.display_message("Unable to connect to the server. Please try again later.")
            self.client_socket = None

    def receive_messages(self):
        while True:
            if not self.client_socket:
                break  # Exit if the socket is None

            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if message:
                    if self.client_window:  # Ensure the window still exists
                        self.client_window.after(0, self.display_message, message)
                else:
                    break
            except (OSError, ConnectionResetError):
                if self.client_window:  # Ensure the window exists before calling after()
                    self.client_window.after(0, self.display_message, "Disconnected from server.")
                if self.client_socket:
                    self.client_socket.close()
                self.client_socket = None
                break

    def send_message(self, msg=None):
        receivers = self.receivers_entry.get()
        if msg:
            message = msg
        else:
            message = self.message_entry.get()
        if message.lower() == EXIT_CODE:
            self.client_socket.send(json.dumps({"receivers": receivers, "message": message}).encode('utf-8'))
        else:
            full_message = {"receivers": receivers, "message": message}
            self.client_socket.send(json.dumps(full_message).encode('utf-8'))
            self.client_window.after(0, self.display_message, f"{self.username}: {message}")
            self.message_entry.delete(0, tk.END)

    def display_message(self, message):
        if self.client_window and self.client_window.winfo_exists():  # Fenster existiert noch?
            self.chat_area.config(state='normal')
            self.chat_area.insert(tk.END, message + '\n')
            self.chat_area.config(state='disabled')

    def is_socket_alive(self):
        try:
            self.client_socket.send(b'')  # Sending empty bytes to check if it's writable
            log("Socket is alive!")
            return True
        except (socket.error, OSError):
            log("Socket is not alive!")
            return False

    def disconnect(self, shutdown=False):
        if self.client_socket:
            if self.is_socket_alive():
                self.send_message(EXIT_CODE)
            self.client_socket.close()
            self.client_socket = None
        if self.client_window:
            self.client_window.destroy()
            self.client_window = None
        if not shutdown:
            main()  # Reopen the start window after client disconnects

# Load the content of a file
def load_file_content(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        return "File not found."
    except Exception as e:
        return str(e)

# Load the color scheme from a JSON file
def load_color_scheme():
    try:
        if os.path.exists(COLOR_SCHEME_FILE):
            return json.loads(load_file_content(COLOR_SCHEME_FILE))
    except json.JSONDecodeError:
        return COLOR_SCHEME

# Save the color scheme to a JSON file
def save_color_scheme():
    with open(COLOR_SCHEME_FILE, 'w') as file:
        json.dump(COLOR_SCHEME, file, indent=4)

# Start the client
def start_client(username):
    global client
    client = ChatClient(username)

def start_client_username(username, start_window):
    start_window.destroy()
    start_client(username)

# Start the server
def start_server_gui():
    global server
    server = ChatServer()

# Start window
def main():
    start_window = tk.Tk()
    start_window.title("Chat Application")
    start_window.geometry("200x200+10+10")
    start_window.configure(bg=COLOR_SCHEME["WINDOW"]["bg"])

    username_label = tk.Label(start_window, text="Username:", fg=COLOR_SCHEME["LABEL"]["fg"], bg=COLOR_SCHEME["LABEL"]["bg"], bd=COLOR_SCHEME["LABEL"]["bd"], relief=COLOR_SCHEME["LABEL"]["relief"])
    username_label.pack(pady=5)
    username_entry = tk.Entry(start_window, fg=COLOR_SCHEME["ENTRY"]["fg"], bg=COLOR_SCHEME["ENTRY"]["bg"], bd=COLOR_SCHEME["ENTRY"]["bd"], relief=COLOR_SCHEME["ENTRY"]["relief"])
    username_entry.pack(pady=5)

    server_button = tk.Button(start_window, text="Start Server", command=lambda: [start_window.destroy(), start_server_gui()], fg=COLOR_SCHEME["BUTTON"]["fg"], bg=COLOR_SCHEME["BUTTON"]["bg"], bd=COLOR_SCHEME["BUTTON"]["bd"], relief=COLOR_SCHEME["BUTTON"]["relief"])
    server_button.pack(pady=10)

    client_button = tk.Button(start_window, text="Start Client", command=lambda: [start_client_username(username_entry.get(), start_window)], fg=COLOR_SCHEME["BUTTON"]["fg"], bg=COLOR_SCHEME["BUTTON"]["bg"], bd=COLOR_SCHEME["BUTTON"]["bd"], relief=COLOR_SCHEME["BUTTON"]["relief"])
    client_button.pack(pady=10)

    start_window.mainloop()

if __name__ == "__main__":
    #save_color_scheme()
    COLOR_SCHEME = load_color_scheme()
    main()

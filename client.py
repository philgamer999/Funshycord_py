import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
import json

EXIT_CODE = "/bye"

class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Client")

        self.client_socket = None

        self.username_label = tk.Label(root, text="Username:")
        self.username_label.pack(side=tk.LEFT)
        self.username_entry = tk.Entry(root)
        self.username_entry.pack(side=tk.LEFT)
        self.login_button = tk.Button(root, text="Login", command=self.set_username)
        self.login_button.pack(side=tk.LEFT)

        self.receivers_label = tk.Label(root, text="Receivers (comma separated):")
        self.receivers_label.pack()
        self.receivers_entry = tk.Entry(root)
        self.receivers_entry.pack()

        self.message_label = tk.Label(root, text="Message:")
        self.message_label.pack()
        self.message_entry = tk.Entry(root)
        self.message_entry.pack()

        self.send_button = tk.Button(root, text="Send", command=self.send_message)
        self.send_button.pack()

        self.disconnect_button = tk.Button(root, text="Disconnect", command=self.disconnect)
        self.disconnect_button.pack()

        self.chat_area = scrolledtext.ScrolledText(root, state='disabled')
        self.chat_area.pack()

        self.connect_to_server()

    def connect_to_server(self):
        host = '127.0.0.1'  # Server IP address
        port = 12345        # Server port

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))

        threading.Thread(target=self.receive_messages).start()

    def set_username(self):
        username = self.username_entry.get()
        self.client_socket.send(json.dumps({"username": username}).encode('utf-8'))

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if message:
                    message_data = json.loads(message)
                    if message_data.get("message") == EXIT_CODE:
                        self.display_message("You have left the chat.")
                        self.disconnect()
                        break
                    self.display_message(message_data.get("message", ""))
                else:
                    break
            except:
                self.display_message("An error occurred!")
                self.client_socket.close()
                break

    def send_message(self):
        receivers = self.receivers_entry.get()
        message = self.message_entry.get()
        if message.lower() == EXIT_CODE:
            self.client_socket.send(json.dumps({"message": message}).encode('utf-8'))
            self.disconnect()
        else:
            full_message = {"receivers": receivers, "message": message}
            self.client_socket.send(json.dumps(full_message).encode('utf-8'))
            self.message_entry.delete(0, tk.END)

    def display_message(self, message):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, message + '\n')
        self.chat_area.config(state='disabled')

    def disconnect(self):
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    client = ChatClient(root)
    root.mainloop()
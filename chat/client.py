import socket
import threading

HOST = "127.0.0.1"
PORT = 5000

def receive_messages(sock):
    while True:
        try:
            msg = sock.recv(1024).decode("utf-8")
            print(msg)
        except:
            print("[!] Déconnecté du serveur")
            sock.close()
            break

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    print("[Connecté au serveur]")
    threading.Thread(target=receive_messages, args=(client,), daemon=True).start()

    while True:
        msg = input("")
        if msg.lower() == "quit":
            break
        client.send(msg.encode("utf-8"))

    client.close()

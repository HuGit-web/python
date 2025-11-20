import socket
import threading

HOST = "127.0.0.1"
PORT = 5000
clients = []

def broadcast(msg, current_client):
    for client in clients:
        if client != current_client:
            client.send(msg)

def handle_client(conn, addr):
    print(f"[+] Nouveau client : {addr}")
    while True:
        try:
            message = conn.recv(1024)
            if not message:
                break
            broadcast(message, conn)
        except:
            break

    print(f"[-] Client déconnecté : {addr}")
    clients.remove(conn)
    conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"[SERVEUR] En écoute sur {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        clients.append(conn)
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.daemon = True
        thread.start()

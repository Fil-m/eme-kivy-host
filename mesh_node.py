import socket
import threading
import json

class MeshNode:
    def __init__(self, port=8001):
        self.port = port
        self.running = False
        self.node_info = {
            "type": "relay",
            "status": "online",
            "capabilities": ["discovery", "sync"]
        }

    def start(self):
        self.running = True
        self.server_thread = threading.Thread(target=self._run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        print(f"Mesh Node started on port {self.port}")

    def _run_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', self.port))
            s.listen(5)
            while self.running:
                try:
                    conn, addr = s.accept()
                    threading.Thread(target=self._handle_client, args=(conn, addr)).start()
                except Exception as e:
                    print(f"Server error: {e}")

    def _handle_client(self, conn, addr):
        with conn:
            try:
                data = conn.recv(1024)
                if data:
                    # Проста відповідь з інформацією про ноду
                    response = json.dumps(self.node_info).encode('utf-8')
                    conn.sendall(response)
            except Exception as e:
                print(f"Client handling error: {e}")

    def stop(self):
        self.running = False

import socket
import threading
from concurrent.futures import ThreadPoolExecutor

def get_local_ip():
    """Отримує локальну IP-адресу пристрою."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print(f"Error getting local IP: {e}")
        return '127.0.0.1'

def check_port(ip, port, timeout=0.3):
    """Перевіряє чи відкритий порт на вказаній IP."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            result = s.connect_ex((ip, port))
            return result == 0
    except Exception:
        return False

def discover_nodes(callback):
    """
    Сканує локальну підмережу на наявність вузлів з відкритим портом 8000.
    """
    def scan():
        try:
            local_ip = get_local_ip()
            print(f"DISCOVERY: Local IP detected as {local_ip}")
            found_nodes = []
            
            # Додаємо localhost відразу
            if check_port('127.0.0.1', 8000):
                found_nodes.append({"name": "Local Node (127.0.0.1)", "ip": "127.0.0.1"})

            if local_ip != '127.0.0.1':
                prefix = '.'.join(local_ip.split('.')[:-1]) + '.'
                print(f"DISCOVERY: Scanning subnet {prefix}0/24")
                # Зменшуємо кількість потоків для Android
                with ThreadPoolExecutor(max_workers=20) as executor:
                    futures = {executor.submit(check_port, prefix + str(i), 8000): str(i) for i in range(1, 255)}
                    for future in futures:
                        try:
                            if future.result():
                                node_ip = prefix + futures[future]
                                print(f"DISCOVERY: Found node at {node_ip}")
                                if node_ip != local_ip:
                                    found_nodes.append({"name": f"Node {node_ip}", "ip": node_ip})
                        except Exception as e:
                            continue
            
            print(f"DISCOVERY: Scan complete. Found {len(found_nodes)} nodes.")
            callback(found_nodes)
        except Exception as e:
            print(f"Scan error: {e}")
            callback([])

    threading.Thread(target=scan, daemon=True).start()

import socket
import threading
from concurrent.futures import ThreadPoolExecutor

def get_local_ip():
    """Отримує локальну IP-адресу пристрою."""
    s = socket.socket(socket.socket.AF_INET, socket.socket.SOCK_DGRAM)
    try:
        # Не обов'язково підключатися реально, просто щоб отримати інтерфейс
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def check_port(ip, port, timeout=0.5):
    """Перевіряє чи відкритий порт на вказаній IP."""
    with socket.socket(socket.socket.AF_INET, socket.socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        try:
            s.connect((ip, port))
            return True
        except:
            return False

def discover_nodes(callback):
    """
    Сканує локальну підмережу на наявність вузлів з відкритим портом 8000.
    Викликає callback(node_list) по завершенню.
    """
    local_ip = get_local_ip()
    if local_ip == '127.0.0.1':
        callback([])
        return

    # Визначаємо підмережу (наприклад, 192.168.1.0/24)
    prefix = '.'.join(local_ip.split('.')[:-1]) + '.'
    found_nodes = []

    def scan():
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = {executor.submit(check_port, prefix + str(i), 8000): str(i) for i in range(1, 255)}
            for future in futures:
                ip_suffix = futures[future]
                if future.result():
                    node_ip = prefix + ip_suffix
                    found_nodes.append({"name": f"Node {node_ip}", "ip": node_ip})
        
        # Додаємо localhost для тестів
        if check_port('127.0.0.1', 8000):
            found_nodes.append({"name": "Local Node", "ip": "127.0.0.1"})
            
        callback(found_nodes)

    threading.Thread(target=scan).start()

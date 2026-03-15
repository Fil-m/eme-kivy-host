import socket
import threading
from concurrent.futures import ThreadPoolExecutor

def get_local_ips():
    """Отримує список усіх локальних IP-адрес пристрою."""
    ips = []
    try:
        # Спроба через socket.getaddrinfo для всіх інтерфейсів
        for addr_info in socket.getaddrinfo(socket.gethostname(), None):
            ip = addr_info[4][0]
            if ip.startswith('10.') or ip.startswith('192.168.') or ip.startswith('172.'):
                if ip not in ips:
                    ips.append(ip)
        
        # Запасний варіант через UDP-конект
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 1))
            ip = s.getsockname()[0]
            if ip not in ips:
                ips.append(ip)
        finally:
            s.close()
            
        return ips if ips else ['127.0.0.1']
    except Exception as e:
        print(f"Error getting local IPs: {e}")
        return ['127.0.0.1']

def check_port(ip, port, timeout=0.5):
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
    Сканує всі локальні підмережі на наявність вузлів з відкритим портом 8000.
    """
    def scan():
        try:
            local_ips = get_local_ips()
            print(f"DISCOVERY: Probable local IPs: {local_ips}")
            found_nodes = []
            
            # Додаємо localhost
            if check_port('127.0.0.1', 8000):
                found_nodes.append({"name": "Local Node (127.0.0.1)", "ip": "127.0.0.1"})

            processed_prefixes = set()
            for local_ip in local_ips:
                if local_ip == '127.0.0.1': continue
                
                prefix = '.'.join(local_ip.split('.')[:-1]) + '.'
                if prefix in processed_prefixes: continue
                processed_prefixes.add(prefix)
                
                print(f"DISCOVERY: Scanning subnet {prefix}0/24")
                with ThreadPoolExecutor(max_workers=50) as executor:
                    futures = {executor.submit(check_port, prefix + str(i), 8000): str(i) for i in range(1, 255)}
                    for future in futures:
                        try:
                            if future.result():
                                node_ip = prefix + futures[future]
                                print(f"DISCOVERY: Found node at {node_ip}")
                                found_nodes.append({"name": f"Node {node_ip}", "ip": node_ip})
                        except Exception:
                            continue
            
            print(f"DISCOVERY: Scan complete. Total nodes: {len(found_nodes)}")
            callback(found_nodes)
        except Exception as e:
            print(f"Scan error: {e}")
            callback([])

    threading.Thread(target=scan, daemon=True).start()

import os
import zipfile
import requests
import subprocess
import sys

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def download_file(url, local_path, progress_callback=None):
    """Завантажує файл з прогресом (з пропуском перевірки SSL для самопідписаних сертифікатів)."""
    try:
        response = requests.get(url, stream=True, verify=False, timeout=30)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, total_size)
        return True
    except Exception as e:
        print(f"Download error: {e}")
        raise e

def install_package(zip_path, extract_to):
    """Розпаковує ZIP та виконує базове налаштування."""
    if not os.path.exists(zip_path):
        return False, "File not found"
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        return True, "Success"
    except Exception as e:
        return False, str(e)

def setup_django(source_dir, data_dir):
    """
    Налаштовує оточення Django та запускає міграції.
    DATA_DIR передається як змінна оточення.
    """
    env = os.environ.copy()
    env['EME_DATA_DIR'] = data_dir
    
    # Спроба запустити міграції
    try:
        manage_path = os.path.join(source_dir, 'manage.py')
        # На Android ми використовуємо sys.executable
        subprocess.run([sys.executable, manage_path, 'migrate'], env=env, check=True)
        return True
    except Exception as e:
        print(f"Migration error: {e}")
        return False

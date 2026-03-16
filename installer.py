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
    import os
    import sys
    
    # Додаємо шлях до сорців у PYTHONPATH
    if source_dir not in sys.path:
        sys.path.insert(0, source_dir)
        
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eme.settings')
    os.environ['EME_DATA_DIR'] = data_dir
    
    try:
        from django.core.management import execute_from_command_line
        print("INSTALLER: Running migrations in-process...")
        execute_from_command_line([sys.argv[0], 'migrate', '--noinput'])
        return True
    except Exception as e:
        print(f"Migration error: {e}")
        return False

def run_server(source_dir, data_dir, port=8000):
    """Запускає Django сервер через Waitress (стабільніше для Android)."""
    import os
    import sys
    
    if source_dir not in sys.path:
        sys.path.insert(0, source_dir)
        
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eme.settings')
    os.environ['EME_DATA_DIR'] = data_dir
    
    try:
        import django
        django.setup()
        
        from django.core.handlers.wsgi import WSGIHandler
        from waitress import serve
        
        print(f"SERVER: Starting Waitress at port {port}...")
        application = WSGIHandler()
        serve(application, host='0.0.0.0', port=port, threads=4)
        
    except Exception as e:
        print(f"Server error: {e}")
        import traceback
        traceback.print_exc()

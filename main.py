import os
import sys
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.utils import platform
from kivy.uix.textinput import TextInput

import discovery
import installer
import mesh_node

# Path for persistent data
if platform == 'android':
    from android.storage import app_storage_path
    BASE_PATH = app_storage_path()
else:
    BASE_PATH = os.getcwd()

DATA_DIR = os.path.join(BASE_PATH, 'data')
SOURCE_DIR = os.path.join(BASE_PATH, 'source')
TEMP_ZIP = os.path.join(BASE_PATH, 'update.zip')

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SOURCE_DIR, exist_ok=True)

class EmeHostUI(BoxLayout):
    def __init__(self, **kwargs):
        super(EmeHostUI, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 10
        self.padding = 20

        # Ініціалізація Mesh Node
        self.mesh = mesh_node.MeshNode(port=8001)
        self.mesh.start()

        self.status_label = Label(text="EME Dynamic Host", font_size='24sp', bold=True)
        self.add_widget(self.status_label)

        self.info_label = Label(text="Статус: Очікування...", font_size='16sp')
        self.add_widget(self.info_label)

        self.progress = ProgressBar(max=100, value=0)
        self.add_widget(self.progress)

        # Ручне введення IP
        self.manual_ip_input = TextInput(
            text=discovery.get_local_ips()[0], 
            hint_text="Введіть IP комп'ютера (напр. 10.29.244.43)",
            multiline=False,
            size_hint=(1, 0.15)
        )
        self.add_widget(self.manual_ip_input)

        self.action_btn = Button(text="Шукати майстер-ноду", size_hint=(1, 0.2))
        self.action_btn.bind(on_press=self.start_discovery)
        self.add_widget(self.action_btn)
        
        self.manual_btn = Button(text="Використати введений IP", size_hint=(1, 0.15))
        self.manual_btn.bind(on_press=self.use_manual_ip)
        self.add_widget(self.manual_btn)
        
        self.mesh_label = Label(text="Mesh Node: Initializing...", font_size='14sp', color=(0.8, 0.8, 0.8, 1))
        self.add_widget(self.mesh_label)
        
        Clock.schedule_once(self.init_mesh, 1)

    def init_mesh(self, dt):
        ips = discovery.get_local_ips()
        self.mesh_label.text = f"Mesh Node: ACTIVE (IPs: {', '.join(ips)})"
        self.mesh_label.color = (0, 1, 0, 1)

    def use_manual_ip(self, instance):
        ip = self.manual_ip_input.text.strip()
        if ip:
            self.found_node_ip = ip
            self.info_label.text = f"Використовується: {ip}\n(Натисніть Клонувати)"
            self.action_btn.text = "Клонувати систему"
            self.action_btn.disabled = False
            self.action_btn.unbind(on_press=self.start_discovery)
            self.action_btn.unbind(on_press=self.begin_install)
            self.action_btn.bind(on_press=self.begin_install)

    def start_discovery(self, instance):
        self.info_label.text = "Сканування мережі..."
        self.action_btn.disabled = True
        discovery.discover_nodes(self.on_discovery_result)

    def on_discovery_result(self, nodes):
        Clock.schedule_once(lambda dt: self._update_discovery_ui(nodes))

    def _update_discovery_ui(self, nodes):
        self.action_btn.disabled = False
        if nodes:
            node = nodes[0]
            self.found_node_ip = node['ip']
            self.info_label.text = f"Знайдено: {node['name']}\nГотовий до клонування."
            self.action_btn.text = "Клонувати систему"
            self.action_btn.unbind(on_press=self.start_discovery)
            self.action_btn.unbind(on_press=self.begin_install)
            self.action_btn.bind(on_press=self.begin_install)
        else:
            self.info_label.text = "Сервер не знайдено.\nПеревірте IP або спробуйте ще раз."
            self.action_btn.text = "Шукати майстер-ноду"

    def begin_install(self, instance):
        self.action_btn.disabled = True
        self.info_label.text = "Завантаження компонентів..."
        threading.Thread(target=self.install_thread, daemon=True).start()

    def install_thread(self):
        url = f"https://{self.found_node_ip}:8000/api/clone/bundle/"
        try:
            print(f"INSTALLER: Starting download from {url}")
            # 1. Download
            installer.download_file(url, TEMP_ZIP, self.on_download_progress)
            
            # 2. Extract
            Clock.schedule_once(lambda dt: setattr(self.info_label, 'text', "Розпакування..."))
            success, msg = installer.install_package(TEMP_ZIP, SOURCE_DIR)
            
            if success:
                # 3. Migrate
                Clock.schedule_once(lambda dt: setattr(self.info_label, 'text', "Налаштування..."))
                installer.setup_django(SOURCE_DIR, DATA_DIR)
                Clock.schedule_once(self.on_install_complete)
            else:
                Clock.schedule_once(lambda dt: self.on_error(f"Помилка розпакування: {msg}"))
                
        except Exception as e:
            print(f"INSTALLER: Critical error: {e}")
            error_msg = str(e)
            Clock.schedule_once(lambda dt: self.on_error(f"Помилка: {error_msg}"))

    def on_download_progress(self, downloaded, total):
        if total > 0:
            percent = (downloaded / total) * 100
            Clock.schedule_once(lambda dt: setattr(self.progress, 'value', percent))

    def on_install_complete(self, dt):
        self.info_label.text = "EME OS успішно встановлено!"
        self.action_btn.text = "Запустити систему"
        self.action_btn.disabled = False
        # Тут можна додати запуск WebView

    def on_error(self, message):
        self.info_label.text = message
        self.action_btn.disabled = False
        self.action_btn.text = "Повторити спробу"

class EmeHostApp(App):
    def build(self):
        return EmeHostUI()

if __name__ == '__main__':
    EmeHostApp().run()

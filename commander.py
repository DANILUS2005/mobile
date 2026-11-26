from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
import subprocess
import threading
import datetime
import urllib.request
import json
import os

class CommanderGUI(BoxLayout):
    def __init__(self, **kwargs):
        super(CommanderGUI, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15

        self.add_widget(Label(text="Field Commander AI Hub", size_hint_y=None, height=50, font_size=22))

        self.input_task = TextInput(
            text='', 
            hint_text="Введите задачу для ИИ (например: Проверь трафик)",
            size_hint_y=None, 
            height=50,
            multiline=False
        )
        self.add_widget(self.input_task)

        self.ai_btn = Button(text="Запустить ИИ-анализ цели", size_hint_y=None, height=60)
        self.ai_btn.bind(on_press=self.on_ai_click)
        self.add_widget(self.ai_btn)

        self.console = TextInput(
            text="[*] Мобильный хаб запущен.\n[*] Подключите целевое устройство по USB OTG.",
            readonly=True,
            multiline=True
        )
        self.add_widget(self.console)

        self.target_device = None
        self.api_key = os.environ.get("OPENAI_API_KEY", "ваш_api_ключ_здесь")
        
        threading.Thread(target=self.scan_target_bg, daemon=True).start()

    def log(self, text):
        Clock.schedule_once(lambda dt: self._append_log(text))

    def _append_log(self, text):
        self.console.text += f"\n{text}"

    def scan_target_bg(self):
        self.log("[*] Поиск целевого устройства по USB...")
        try:
            result = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=True)
            lines = result.stdout.strip().split('\n')[1:]
            devices = [line.split('\t')[0] for line in lines if '\tdevice' in line]
            if devices:
                self.target_device = devices[0]
                self.log(f"[+] Цель захвачена: {self.target_device}")
            else:
                self.log("[-] Устройства не найдены. Проверьте USB OTG и отладку.")
        except Exception as e:
            self.log(f"[-] Ошибка сканирования: {e}")

    def execute_remote(self, cmd):
        if not self.target_device:
            return "[-] Цель не подключена."
        try:
            res = subprocess.run(
                ["adb", "-s", self.target_device, "shell", cmd],
                capture_output=True, text=True, timeout=15
            )
            return res.stdout.strip()
        except Exception as e:
            return f"[-] Ошибка выполнения: {e}"

    def on_ai_click(self, instance):
        task = self.input_task.text.strip()
        if not task:
            self.log("[-] Введите задачу для ИИ!")
            return
        
        self.input_task.text = ""
        self.log(f"\n> Задача: {task}")
        threading.Thread(target=self.run_ai_task, args=(task,), daemon=True).start()

    def run_ai_task(self, task):
        self.log("[*] Сбор телеметрии с целевого устройства...")
        telemetry = {
            "timestamp": str(datetime.datetime.now()),
            "device_id": self.target_device,
            "os_version": self.execute_remote("getprop ro.build.version.release"),
            "model": self.execute_remote("getprop ro.product.model"),
            "battery": self.execute_remote("dumpsys battery | grep level"),
            "active_connections": self.execute_remote("netstat -an | grep ESTABLISHED"),
            "running_processes": self.execute_remote("ps -A")
        }

        context = f"""
Ты — кибернетический помощник для полевой диагностики устройств.
Устройство: {telemetry['model']} (Android {telemetry['os_version']})
Батарея: {telemetry['battery']}
Трафик (соединения):
{telemetry['active_connections']}
Процессы:
{telemetry['running_processes'][:600]}

ЗАДАЧА ПОЛЬЗОВАТЕЛЬЯ:
{task}
"""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": context}],
            "temperature": 0.3
        }

        self.log("[*] Запрос к ИИ-аналитику...")
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                answer = res_data['choices'][0]['message']['content']
                self.log(f"\n[ОТВЕТ ИИ]:\n{answer}\n")
        except Exception as e:
            self.log(f"[-] Ошибка ИИ API: {e}")

class FieldCommanderApp(App):
    def build(self):
        self.title = "Field Commander AI"
        return CommanderGUI()

if __name__ == '__main__':
    FieldCommanderApp().run()

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
import subprocess
import threading
import datetime
import urllib.request
import json
import os

class CommanderUI(BoxLayout):
    def __init__(self, **kwargs):
        super(CommanderUI, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 15
        self.spacing = 10

        # Заголовок
        self.add_widget(Label(text="[ Field Commander AI Hub ]", size_hint_y=None, height=40, font_size=20))

        # Однострочное поле для ввода задачи для ИИ или команды
        self.input_field = TextInput(
            text='', 
            hint_text="Введи задачу для ИИ (например: Проверь трафик) или cmd <команда>",
            size_hint_y=None, 
            height=50,
            multiline=False
        )
        self.add_widget(self.input_field)

        # Кнопка отправки
        self.send_btn = Button(text="Выполнить / Спросить ИИ", size_hint_y=None, height=60)
        self.send_btn.bind(on_press=self.on_submit)
        self.add_widget(self.send_btn)

        # Лог-консоль (вывод результатов)
        self.console = TextInput(
            text="[*] Инициализация мобильного хаба...\n[*] Подключите целевое устройство по USB OTG.",
            readonly=True,
            multiline=True
        )
        self.add_widget(self.console)

        self.target_device = None
        self.api_key = os.environ.get("OPENAI_API_KEY", "твой_api_ключ_здесь")
        
        # Сканируем устройство при старте в фоновом потоке
        threading.Thread(target=self.scan_target_bg, daemon=True).start()

    def log(self, text):
        Clock.schedule_once(lambda dt: self._append_log(text))

    def _append_log(self, text):
        self.console.text += f"\n{text}"

    def scan_target_bg(self):
        self.log("[*] Поиск целевого устройства по USB...")
        try:
            result = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=True)
            lines = result.stdout.strip().split('\n')[1:]
            devices = [line.split('\t')[0] for line in lines if '\tdevice' in line]
            if devices:
                self.target_device = devices[0]
                self.log(f"[+] Цель захвачена: {self.target_device}")
            else:
                self.log("[-] Устройства не найдены. Проверьте USB OTG и отладку.")
        except Exception as e:
            self.log(f"[-] Ошибка сканирования: {e}")

    def execute_remote(self, cmd):
        if not self.target_device:
            return "[-] Ошибка: Цель не выбрана или не подключена."
        try:
            res = subprocess.run(
                ["adb", "-s", self.target_device, "shell", cmd],
                capture_output=True, text=True, timeout=15
            )
            return res.stdout.strip()
        except Exception as e:
            return f"[-] Ошибка выполнения: {e}"

    def on_submit(self, instance):
        user_text = self.input_field.text.strip()
        if not user_text:
            return
        
        self.input_field.text = ""
        self.log(f"\n> {user_text}")
        
        # Запускаем задачу в фоновом потоке, чтобы не вешать интерфейс планшета
        threading.Thread(target=self.process_command, args=(user_text,), daemon=True).start()

    def process_command(self, text):
        if text.startswith('cmd '):
            cmd = text[4:]
            res = self.execute_remote(cmd)
            self.log(f"\n[Результат shell]:\n{res}")
        else:
            # ИИ Анализ
            self.log("[*] Сбор телеметрии и запрос к ИИ...")
            telemetry = {
                "timestamp": str(datetime.datetime.now()),
                "device_id": self.target_device,
                "os_version": self.execute_remote("getprop ro.build.version.release"),
                "model": self.execute_remote("getprop ro.product.model"),
                "battery": self.execute_remote("dumpsys battery | grep level"),
                "active_connections": self.execute_remote("netstat -an | grep ESTABLISHED"),
                "running_processes": self.execute_remote("ps -A")
            }

            context = f"""
Ты — кибернетический помощник для полевой диагностики устройств.
Устройство: {telemetry['model']} (Android {telemetry['os_version']})
Батарея: {telemetry['battery']}
Трафик (соединения):
{telemetry['active_connections']}
Процессы:
{telemetry['running_processes'][:600]}

ЗАДАЧА ПОЛЬЗОВАТЕЛЯ:
{text}
"""
            # Запрос к API
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
            payload = {
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": context}],
                "temperature": 0.3
            }

            try:
                req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
                with urllib.request.urlopen(req) as response:
                    res_data = json.loads(response.read().decode('utf-8'))
                    answer = res_data['choices'][0]['message']['content']
                    self.log(f"\n[Ответ ИИ]:\n{answer}")
            except Exception as e:
                self.log(f"[-] Ошибка ИИ: {e}")

class FieldCommanderApp(App):
    def build(self):
        self.title = "Field Commander AI"
        return CommanderUI()

if __name__ == '__main__':
    FieldCommanderApp().run()


import subprocess
import datetime
import sys

class FieldCommander:
    def __init__(self):
        print("[*] Инициализация Field Commander Hub...")
        self.target_device = None

    def scan_target(self):
        """Поиск и выбор подключенного по USB устройства"""
        try:
            result = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=True)
            lines = result.stdout.strip().split('\n')[1:]
            devices = [line.split('\t')[0] for line in lines if '\tdevice' in line]
            
            if not devices:
                print("[-] Целевые устройства не обнаружены по проводу.")
                return False
            
            self.target_device = devices[0]
            print(f"[+] Цель захвачена: {self.target_device}")
            return True
        except Exception as e:
            print(f"[-] Ошибка сканирования шины: {e}")
            return False

    def execute_remote(self, cmd):
        """Выполнение произвольной команды на целевом устройстве"""
        if not self.target_device:
            return "[-] Ошибка: Цель не выбрана."
        
        try:
            res = subprocess.run(
                ["adb", "-s", self.target_device, "shell", cmd],
                capture_output=True, text=True, timeout=15
            )
            return res.stdout.strip()
        except Exception as e:
            return f"[-] Сбой выполнения: {e}"

    def gather_telemetry(self):
        """Сбор полного «паспорта» и состояния целевого устройства"""
        print("[*] Сбор телеметрии с целевого устройства...")
        return {
            "timestamp": str(datetime.datetime.now()),
            "device_id": self.target_device,
            "os_version": self.execute_remote("getprop ro.build.version.release"),
            "model": self.execute_remote("getprop ro.product.model"),
            "battery": self.execute_remote("dumpsys battery | grep level"),
            "active_connections": self.execute_remote("netstat -an | grep ESTABLISHED"),
            "running_processes": self.execute_remote("ps -A")
        }

    def export_for_ai(self):
        """Форматирует данные для отправки ИИ (для анализа)"""
        data = self.gather_telemetry()
        report = f"""
=== ОТЧЕТ РАЗВЕДКИ ЦЕЛИ ===
Время: {data['timestamp']}
Модель: {data['model']} (Android {data['os_version']})
Батарея: {data['battery']}

--- СЕТЕВЫЕ СОЕДИНЕНИЯ (ТРАФИК) ---
{data['active_connections']}

--- ТОП ПРОЦЕССОВ ---
{data['running_processes'][:800]}
===========================
"""
        return report

    def interactive_loop(self):
        """Интерактивный режим управления с планшета"""
        if not self.scan_target():
            print("[-] Подключи устройство по проводу и включи отладку!")
            return

        print("\n" + "="*40)
        print(" ИНТЕРАКТИВНЫЙ РЕЖИМ FIELD COMMANDER АКТИВЕН")
        print(" Команды:")
        print("   - 'scan' : Собрать полный отчет разведки (для ИИ)")
        print("   - 'cmd <команда>' : Выполнить shell-команду на цели (например: cmd ls -l)")
        print("   - 'exit' : Выход")
        print("="*40 + "\n")

        while True:
            try:
                user_input = input("Commander> ").strip()
                if not user_input:
                    continue
                
                if user_input.lower() == 'exit':
                    print("[*] Выход из режима управления.")
                    break
                elif user_input.lower() == 'scan':
                    print(self.export_for_ai())
                elif user_input.startswith('cmd '):
                    remote_cmd = user_input[4:]
                    output = self.execute_remote(remote_cmd)
                    print(f"\n[Результат от цели]:\n{output}\n")
                else:
                    print("[-] Неизвестная команда. Введи 'scan', 'cmd <команда>' или 'exit'.")
            except KeyboardInterrupt:
                print("\n[*] Прервано пользователем.")
                break

if __name__ == "__main__":
    hub = FieldCommander()
    hub.interactive_loop()

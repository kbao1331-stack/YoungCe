import paho.mqtt.client as mqtt
import json
import time
import threading
import random
import hashlib
import ssl
import os
import re
from typing import Optional, Callable
from urllib.parse import urlparse

# ================== HÀM TIỆN ÍCH ==================

def generate_offline_threading_id() -> str:
    """Tạo ID offline threading giống Facebook"""
    return str(int(time.time() * 1000)) + str(random.randint(1000, 9999))

def json_minimal(data) -> str:
    """Chuyển dict -> JSON rút gọn"""
    return json.dumps(data, separators=(",", ":"))

def parse_cookie_string(cookie_string: str) -> dict:
    """Parse cookie string thành dict"""
    cookies = {}
    for part in cookie_string.split(";"):
        if "=" in part:
            key, value = part.strip().split("=", 1)
            cookies[key] = value
    return cookies

def generate_session_id() -> str:
    """Tạo session id"""
    return hashlib.md5(str(time.time()).encode()).hexdigest()

def generate_client_id() -> str:
    """Tạo client id random"""
    return str(random.randint(10**14, 10**15 - 1))

# ================== GIAO DIỆN (UI) ==================

def rainbow_text(text, offset=0):
    colors = [
        (255, 0, 0), (255, 140, 0), (255, 215, 0), (0, 255, 0),
        (0, 255, 200), (0, 150, 255), (138, 43, 226), (255, 20, 147)
    ]
    result = ""
    for i, char in enumerate(text):
        idx = (i + offset * 2) % len(colors)
        r, g, b = colors[idx]
        result += f"\033[38;2;{r};{g};{b}m{char}"
    result += "\033[0m"
    return result

def print_rainbow_banner(offset=0):
    lines = [
        "┌──────────────────────── Info ───────────────────────┐",
        " ➜ Admin: YOUNGCE",
        " ➜ Box: AE HẮC LINH",
        " ➜ CHỨC NĂNG: AUTO SET THEME MESSENGER (MQTT) 💥",
        "└─────────────────────────────────────────────────────┘",
    ]
    for line in lines:
        print(rainbow_text(line, offset=offset))

def animate_banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    for i in range(50):
        print_rainbow_banner(offset=i)
        time.sleep(0.02)
    os.system('clear' if os.name == 'posix' else 'cls')
    print_rainbow_banner(offset=25)

# ================== DANH SÁCH THEMES ==================

THEMES = [
    {"id": "3650637715209675", "name": "Besties"},
    {"id": "769656934577391", "name": "Women's History Month"},
    {"id": "702099018755409", "name": "Dune: Part Two"},
    {"id": "1480404512543552", "name": "Avatar: The Last Airbender"},
    {"id": "741311439775765", "name": "Love"},
    {"id": "2317258455139234", "name": "One Piece"},
    {"id": "6685081604943997", "name": "1989 (Taylor's Version)"},
    {"id": "3273938616164733", "name": "Classic"},
    {"id": "736591620215564", "name": "Ocean"},
    {"id": "193497045377796", "name": "Grape"}
    # ... (Bạn có thể thêm các ID khác vào đây)
]

# ================== MQTT CLIENT CORE ==================

class MQTTThemeClient:
    def __init__(self, cookies: str):
        self.cookies = cookies
        self.mqtt_client = None
        self.is_connected = False
        self.user_id = None
        self.ws_req_number = 0
        self.ws_task_number = 0
        
        cookie_dict = parse_cookie_string(cookies)
        if "c_user" in cookie_dict:
            self.user_id = cookie_dict["c_user"]
        else:
            raise ValueError("Không tìm thấy user ID trong cookies")
    
    def connect(self):
        if self.is_connected: return
            
        session_id = generate_session_id()
        client_id = generate_client_id()
        
        user_info = {
            "u": self.user_id, "s": session_id, "chat_on": True, "fg": False,
            "d": client_id, "ct": "websocket", "aid": "219994525426954",
            "cp": 3, "ecp": 10, "no_auto_fg": True
        }
        
        host = f"wss://edge-chat.facebook.com/chat?sid={session_id}&cid={client_id}"
        cookie_dict = parse_cookie_string(self.cookies)
        cookie_str = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])
        
        self.mqtt_client = mqtt.Client(client_id="mqttwsclient", clean_session=True, 
                                      protocol=mqtt.MQTTv31, transport="websockets")
        
        self.mqtt_client.tls_set(cert_reqs=ssl.CERT_NONE, tls_version=ssl.PROTOCOL_TLSv1_2)
        self.mqtt_client.tls_insecure_set(True)
        self.mqtt_client.username_pw_set(username=json_minimal(user_info))
        
        parsed_host = urlparse(host)
        self.mqtt_client.ws_set_options(
            path=f"{parsed_host.path}?{parsed_host.query}",
            headers={
                "Cookie": cookie_str,
                "Origin": "https://www.facebook.com",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }
        )
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0: self.is_connected = True
        
        self.mqtt_client.on_connect = on_connect
        self.mqtt_client.connect("edge-chat.facebook.com", 443, 60)
        self.mqtt_client.loop_start()
        
        # Chờ kết nối
        for _ in range(50):
            if self.is_connected: break
            time.sleep(0.1)

    def disconnect(self):
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()

    def set_theme(self, thread_id: str):
        if not self.is_connected: return
        
        theme = random.choice(THEMES)
        self.ws_req_number += 1
        self.ws_task_number += 1
        
        task_payload = {"thread_key": thread_id, "theme_fbid": theme["id"], "sync_group": 1}
        task = {"label": "43", "payload": json_minimal(task_payload), "queue_name": "thread_theme", "task_id": self.ws_task_number}
        
        content = {
            "app_id": "2220391788200892",
            "payload": json_minimal({
                "epoch_id": int(generate_offline_threading_id()),
                "tasks": [task],
                "version_id": "25095469420099952"
            }),
            "request_id": self.ws_req_number,
            "type": 3
        }
        
        self.mqtt_client.publish("/ls_req", json_minimal(content), qos=1)
        return theme['name']

# ================== LUỒNG ĐIỀU KHIỂN ==================

stop_flag = False

def command_listener():
    global stop_flag
    while not stop_flag:
        try:
            cmd = input().strip().lower()
            if cmd == 's':
                stop_flag = True
                print(rainbow_text("\n[!] ĐANG DỪNG HỆ THỐNG..."))
                break
        except EOFError:
            break

def main():
    global stop_flag
    animate_banner()

    # Nhập ID Box
    box_id = input(rainbow_text("Nhập ID box: ")).strip()
    
    # Nhập Cookie
    cookie = input(rainbow_text("Nhập cookie: ")).strip()

    # Nhập Delay
    try:
        val = input(rainbow_text("Delay mỗi lần set (giây, mặc định 0.3): ") or "0.3")
        delay = float(val)
    except:
        delay = 0.3

    print(rainbow_text("\n💥 BẮT ĐẦU SET THEME VÔ HẠN – Gõ 's' để dừng 🔥\n"))

    # Hàm chạy set theme chính
    def run_set_theme():
        try:
            client = MQTTThemeClient(cookie)
            client.connect()
            count = 0
            while not stop_flag:
                theme_name = client.set_theme(box_id)
                count += 1
                ts = time.strftime("%H:%M:%S")
                print(f"\r{rainbow_text(f'[{ts}] Lần: {count} | Theme: {theme_name} | Box: {box_id}', offset=count)}", end="")
                time.sleep(delay)
        except Exception as e:
            print(f"\nLỗi hệ thống: {e}")
        finally:
            try: client.disconnect()
            except: pass

    # Khởi chạy các luồng
    t_spam = threading.Thread(target=run_set_theme, daemon=True)
    t_spam.start()

    t_cmd = threading.Thread(target=command_listener, daemon=True)
    t_cmd.start()

    while t_spam.is_alive() and not stop_flag:
        time.sleep(0.5)

    print(rainbow_text("\nChương trình đã kết thúc."))

if __name__ == "__main__":
    main()

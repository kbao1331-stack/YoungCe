import json
import time
import random
import os
import threading
import ssl
import requests
from urllib.parse import urlparse

# --- IMPORT TỪ FILE UTILS CỦA BẠN ---
try:
    from module.utils import (
        parse_cookie_string,
        generate_offline_threading_id,
        generate_session_id,
        generate_client_id,
        json_minimal,
        gen_threading_id,
        get_headers,
        formAll,
        mainRequests,
        dataGetHome,
        fbTools,
        get_from,
        dataSplit,
        clearHTML
    )
except ImportError:
    print("Lỗi: Không tìm thấy module.utils. Vui lòng kiểm tra file utils.py")

import paho.mqtt.client as mqtt

# --- PHẦN GIAO DIỆN (BANNER) ---

def rainbow_text(text, offset=0):
    colors = [(255, 0, 0), (255, 140, 0), (255, 215, 0), (0, 255, 0),
              (0, 255, 200), (0, 150, 255), (138, 43, 226), (255, 20, 147)]
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
        " ➜ Chức năng: SPAM POLL MESSENGER (MQTT) 🔥",
        "└─────────────────────────────────────────────────────┘",
    ]
    for line in lines:
        print(rainbow_text(line, offset=offset))

def animate_banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    for i in range(20):
        print_rainbow_banner(offset=i)
        time.sleep(0.04)
    print_rainbow_banner(offset=25)

# --- LOGIC MQTT & POLL (GIỮ NGUYÊN TỪ SOURCE CỦA BẠN) ---

active_senders = {}

class MessageSender:
    def __init__(self, fb_tools_instance, dataFB, fb_instance):
        self.fb_tools = fb_tools_instance
        self.dataFB = dataFB
        self.fb = fb_instance
        self.mqtt = None
        self.ws_req_number = 0
        self.ws_task_number = 0
        self.last_seq_id = None
        self.sync_token = None
        self.connected = False
        self.user_id = dataFB.get("FacebookID")
        self.session_id = generate_session_id()
        self.client_id = generate_client_id()
        
    def get_last_seq_id(self):
        try:
            if self.fb_tools.getAllThreadList():
                self.last_seq_id = self.fb_tools.last_seq_id
                return True
            return False
        except: return False
    
    def connect_mqtt(self):
        try:
            user = {
                "a": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "u": self.user_id, "s": self.session_id, "chat_on": True, "fg": False,
                "d": self.client_id, "ct": "websocket", "aid": "219994525426954",
                "cp": 3, "ecp": 10, "st": [], "pm": [], "dc": "", "no_auto_fg": True, "gas": None, "pack": []
            }
            host = f"wss://edge-chat.facebook.com/chat?sid={self.session_id}&cid={self.client_id}"
            cookie_dict = parse_cookie_string(self.dataFB["cookieFacebook"])
            cookie_str = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])
            
            headers = {
                "Cookie": cookie_str, "Origin": "https://www.facebook.com",
                "User-Agent": "Mozilla/5.0", "Host": "edge-chat.facebook.com"
            }
            
            self.mqtt = mqtt.Client(client_id="mqttwsclient", clean_session=True, protocol=mqtt.MQTTv31, transport="websockets")
            self.mqtt.tls_set(certfile=None, keyfile=None, cert_reqs=ssl.CERT_NONE, tls_version=ssl.PROTOCOL_TLSv1_2)
            self.mqtt.tls_insecure_set(True)
            self.mqtt.on_connect = self._on_connect
            self.mqtt.username_pw_set(username=json_minimal(user))
            
            parsed_host = urlparse(host)
            self.mqtt.ws_set_options(path=f"{parsed_host.path}?{parsed_host.query}", headers=headers)
            self.mqtt.connect(host="edge-chat.facebook.com", port=443, keepalive=10)
            self.mqtt.loop_start()
            
            timeout = 15
            while not self.connected and timeout > 0:
                time.sleep(0.5)
                timeout -= 0.5
            return self.connected
        except: return False

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0: self.connected = True

    def send_poll(self, thread_id, question, options):
        if not self.connected: return False
        try:
            self.ws_req_number += 1
            self.ws_task_number += 1
            task_payload = {"question_text": question, "thread_key": int(thread_id), "options": options, "sync_group": 1}
            task = {"label": "163", "payload": json.dumps(task_payload), "queue_name": "poll_creation", "task_id": self.ws_task_number}
            content = {
                "app_id": "2220391788200892",
                "payload": json.dumps({"tasks": [task], "epoch_id": int(generate_offline_threading_id()), "version_id": "7158486590867448"}),
                "request_id": self.ws_req_number, "type": 3
            }
            self.mqtt.publish(topic="/ls_req", payload=json.dumps(content), qos=1)
            return True
        except: return False

    def stop(self):
        if self.mqtt: self.mqtt.disconnect(); self.connected = False

class facebook_api:
    def __init__(self, cookie):
        self.cookie = cookie
        self.dataFB = dataGetHome(cookie)
        self.user_id = self.dataFB.get("FacebookID")
        self.fb_dtsg = self.dataFB.get("fb_dtsg")
        self.rev = self.dataFB.get("clientRevision")
        self.jazoest = self.dataFB.get("jazoest")

# --- HÀM CHẠY CHÍNH (START NHAY POLL) ---

stop_flag = False

def start_nhay_poll_func(cookie, idbox, delay_str, folder_name):
    global stop_flag
    delay = float(delay_str)
    try:
        fb = facebook_api(cookie)
        if not fb.user_id: 
            print(rainbow_text("[X] Cookie die hoặc lỗi!")); return

        fb_tools_instance = fbTools(fb.dataFB)
        sender = MessageSender(fb_tools_instance, fb.dataFB, fb)
        
        if not sender.get_last_seq_id() or not sender.connect_mqtt():
            print(rainbow_text("[X] Không thể kết nối MQTT!")); return

        active_senders[folder_name] = sender
        nhay_path = folder_name # Sử dụng input file làm đường dẫn file ngôn

        print(rainbow_text(f"\n[!] BẮT ĐẦU SPAM POLL BOX: {idbox}"))
        
        while not stop_flag:
            if not os.path.exists(nhay_path):
                print(rainbow_text(f"[X] File {nhay_path} không tồn tại!")); break
            
            with open(nhay_path, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]

            if len(lines) < 3:
                print(rainbow_text("[!] File cần ít nhất 3 dòng.")); time.sleep(5); continue

            for line in lines:
                if stop_flag: break
                title = line
                available_options = [opt for opt in lines if opt != title]
                options = random.sample(available_options, 2)
                
                success = sender.send_poll(idbox, title, options)
                status = "OK" if success else "FAIL"
                print(f"\r{rainbow_text(f'[{status}] Đã gửi Poll: {title[:20]}... | Delay: {delay}s')}", end="")
                time.sleep(delay)

        sender.stop()
    except Exception as e:
        print(f"\nLỗi: {e}")

# --- MAIN GIAO DIỆN ---

def main():
    animate_banner()
    
    # Input các tham số theo yêu cầu
    cookie = input(rainbow_text("Nhập Cookie Facebook: ")).strip()
    idbox = input(rainbow_text("Nhập ID Box (Thread ID): ")).strip()
    delay = input(rainbow_text("Nhập Delay (giây, VD 10): ")).strip() or "10"
    file_ngon = input(rainbow_text("Nhập tên file nội dung (VD: ngon.txt): ")).strip()

    if not cookie or not idbox or not file_ngon:
        print(rainbow_text("Thiếu thông tin, thoát..."))
        return

    # Chạy spam trong 1 thread riêng để không bị block giao diện
    thr = threading.Thread(target=start_nhay_poll_func, args=(cookie, idbox, delay, file_ngon))
    thr.daemon = True
    thr.start()

    print(rainbow_text("\n[Phím nóng] Gõ 's' để dừng chương trình."))
    while True:
        cmd = input().lower()
        if cmd == 's':
            global stop_flag
            stop_flag = True
            print(rainbow_text("Đang dừng..."))
            time.sleep(2)
            break

if __name__ == "__main__":
    main()

import requests
import json
import time
import threading
import re
import os
import random
import ssl
from bs4 import BeautifulSoup
import paho.mqtt.client as mqtt
from urllib.parse import urlparse
from typing import Callable, Optional

# Giữ nguyên import từ utils của bạn
from module.utils import (
    parse_cookie_string,
    generate_offline_threading_id,
    generate_session_id,
    generate_client_id,
    json_minimal,
    get_headers,
    dataGetHome
)

# --- PHẦN CLASS MQTT (TÍCH HỢP 100%) ---

class FacebookMQTTShareContact:
    def __init__(self, cookies: str, options: dict = None):
        if options is None:
            options = {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
                "online": True,
            }
        self.cookies = cookies
        self.options = options
        try:
            self.dataFB = dataGetHome(cookies)
        except:
            self.dataFB = {}
        
        cookie_dict = parse_cookie_string(cookies)
        self.user_id = cookie_dict.get("c_user")
        if not self.user_id:
            raise Exception("Cookie không hợp lệ (thiếu c_user)")
        
        self.mqtt_client = None
        self.req_callbacks = {}
        self.req_id_counter = 0
        self.connected = False
        
    def connect(self):
        session_id = generate_session_id()
        client_id = generate_client_id()
        user_config = {
            "a": self.options["user_agent"], "u": self.user_id, "s": session_id,
            "chat_on": self.options["online"], "fg": False, "d": client_id,
            "ct": "websocket", "aid": "219994525426954", "mqtt_sid": "",
            "cp": 3, "ecp": 10, "st": [], "pm": [], "dc": "", "no_auto_fg": True, "gas": None, "pack": [],
        }
        host = f"wss://edge-chat.facebook.com/chat?sid={session_id}&cid={client_id}"
        cookie_dict = parse_cookie_string(self.cookies)
        cookie_str = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])
        
        headers = {
            "Cookie": cookie_str,
            "Origin": "https://www.facebook.com",
            "User-Agent": self.options["user_agent"],
            "Referer": "https://www.facebook.com/",
            "Host": "edge-chat.facebook.com",
        }

        self.mqtt_client = mqtt.Client(client_id="mqttwsclient", clean_session=True, protocol=mqtt.MQTTv31, transport="websockets")
        self.mqtt_client.tls_set(cert_reqs=ssl.CERT_NONE, tls_version=ssl.PROTOCOL_TLSv1_2)
        self.mqtt_client.tls_insecure_set(True)
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_message = self._on_message
        self.mqtt_client.username_pw_set(username=json_minimal(user_config))
        
        parsed_host = urlparse(host)
        self.mqtt_client.ws_set_options(path=f"{parsed_host.path}?{parsed_host.query}", headers=headers)
        self.mqtt_client.connect(host=headers["Host"], port=443, keepalive=10)
        self.mqtt_client.loop_start()

        start_time = time.time()
        while not self.connected and (time.time() - start_time) < 10:
            time.sleep(0.1)
        if not self.connected: raise Exception("Kết nối MQTT thất bại")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            client.subscribe("/ls_resp", qos=1)
            client.publish(topic="/ls_app_settings", payload=json_minimal({"ls_fdid": "", "ls_sv": "6928813347213944"}), qos=1)

    def _on_message(self, client, userdata, msg):
        if msg.topic == "/ls_resp":
            try:
                parsed = json.loads(msg.payload.decode("utf-8"))
                rid = parsed.get("request_id")
                if rid in self.req_callbacks:
                    self.req_callbacks[rid]({"success": True}, None)
                    del self.req_callbacks[rid]
            except: pass

    def share_contact(self, contact_id, thread_id, text=""):
        if not self.connected: return False
        self.req_id_counter += 1
        request_id = self.req_id_counter
        task = {
            "label": 359,
            "payload": json_minimal({"contact_id": contact_id, "sync_group": 1, "text": text, "thread_id": thread_id}),
            "queue_name": "xma_open_contact_share",
            "task_id": random.randint(0, 1000),
            "failure_count": None,
        }
        message = {
            "app_id": "2220391788200892",
            "payload": json_minimal({"tasks": [task], "epoch_id": generate_offline_threading_id(), "version_id": "7214102258676893"}),
            "request_id": request_id,
            "type": 3
        }
        res = self.mqtt_client.publish(topic="/ls_req", payload=json_minimal(message), qos=1)
        return res.rc == mqtt.MQTT_ERR_SUCCESS

    def disconnect(self):
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()

# --- PHẦN GIAO DIỆN & LOGIC ĐIỀU KHIỂN ---

def rainbow_text(text, offset=0):
    colors = [(255, 0, 0), (255, 140, 0), (255, 215, 0), (0, 255, 0), (0, 255, 200), (0, 150, 255), (138, 43, 226), (255, 20, 147)]
    result = ""
    for i, char in enumerate(text):
        idx = (i + offset * 2) % len(colors)
        r, g, b = colors[idx]
        result += f"\033[38;2;{r};{g};{b}m{char}"
    return result + "\033[0m"

def print_banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    banner = [
        "┌─────────────────────────────────────────────────────┐",
        "  ➜ ADMIN: YOUNGCE (MOD MQTT SHARE CONTACT)",
        "  ➜ CHỨC NĂNG: SPAM SHARE CONTACT VÔ HẠN 💥",
        "└─────────────────────────────────────────────────────┘",
    ]
    for i, line in enumerate(banner): print(rainbow_text(line, i))

stop_flag = False
current_delay = 0.5
messages_content = ""

def load_file_content(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except: return None

def spam_loop(messengers, thread_ids, contact_id):
    global stop_flag, current_delay, messages_content
    counter = 0
    while not stop_flag:
        counter += 1
        for tid in thread_ids:
            if stop_flag: break
            for m in messengers:
                if stop_flag: break
                success = m.share_contact(contact_id, tid, messages_content)
                status = "OK" if success else "X"
                ts = time.strftime("%H:%M:%S")
                print(f"\r{rainbow_text(f'[{status}] {ts} | Box: {tid} | Lần: {counter} | Delay: {current_delay}s', counter)}", end="")
                time.sleep(current_delay)

def main():
    global stop_flag, current_delay, messages_content
    print_banner()

    # 1. Nhập Đa Cookie
    cookies_list = []
    print(rainbow_text("Nhập danh sách Cookie (Xong bấm Enter trống):"))
    while True:
        ck = input(rainbow_text("> ")).strip()
        if not ck: break
        cookies_list.append(ck)

    # 2. Nhập Đa ID Box (Thread ID)
    thread_ids = []
    print(rainbow_text("\nNhập danh sách ID Box (Xong bấm Enter trống):"))
    while True:
        tid = input(rainbow_text("> ")).strip()
        if not tid: break
        thread_ids.append(tid)

    # 3. Nhập ID Contact cần share
    contact_id = input(rainbow_text("\nNhập ID Contact cần share: ")).strip()

    # 4. Nhập File ngôn (Message Text)
    while True:
        fn = input(rainbow_text("\nNhập tên file chứa nội dung (VD: ngon.txt): ")).strip()
        content = load_file_content(fn)
        if content:
            messages_content = content
            print(rainbow_text(f"[OK] Đã load file. Độ dài: {len(content)} ký tự"))
            break
        print(rainbow_text("[Lỗi] File không tồn tại hoặc rỗng!"))

    # 5. Nhập Delay
    try:
        current_delay = float(input(rainbow_text("\nNhập Delay (giây, mặc định 0.5): ") or "0.5"))
    except: current_delay = 0.5

    # Khởi tạo kết nối MQTT cho từng cookie
    messengers = []
    print(rainbow_text("\n--- Đang khởi tạo kết nối MQTT ---"))
    for i, ck in enumerate(cookies_list):
        try:
            m = FacebookMQTTShareContact(ck)
            m.connect()
            messengers.append(m)
            print(rainbow_text(f"[Cookie {i+1}] Kết nối thành công!"))
        except Exception as e:
            print(rainbow_text(f"[Cookie {i+1}] Lỗi: {e}"))

    if not messengers:
        print(rainbow_text("\n[!] Không có kết nối nào thành công. Thoát.")); return

    print(rainbow_text("\n💥 BẮT ĐẦU SPAM SHARE CONTACT... (Bấm Ctrl+C để dừng)"))
    
    # Chạy vòng lặp spam
    try:
        spam_loop(messengers, thread_ids, contact_id)
    except KeyboardInterrupt:
        stop_flag = True
        print(rainbow_text("\n[!] Đang dừng hệ thống..."))

    for m in messengers: m.disconnect()
    print(rainbow_text("Đã dừng."))

if __name__ == "__main__":
    main()
    
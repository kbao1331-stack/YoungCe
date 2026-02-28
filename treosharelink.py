import time
import threading
import os
import json
import random
import paho.mqtt.client as mqtt
from urllib.parse import urlparse
import ssl
from typing import Callable, Optional

# Giữ nguyên import từ utils như bạn yêu cầu
from module.utils import (
    parse_cookie_string,
    generate_offline_threading_id,
    generate_session_id,
    generate_client_id,
    json_minimal,
    get_headers,
    dataGetHome
)

# --- 100% CODE MODULE FACEBOOKMQTTSHARELINK ---

class FacebookMQTTShareLink:
    """Facebook MQTT client for sharing link functionality"""
    
    def __init__(self, cookies: str, options: dict = None):
        """Initialize MQTT client for sharing links
        
        Args:
            cookies: Facebook cookies string
            options: Configuration options
        """
        if options is None:
            options = {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
                "online": True,
            }
        
        self.cookies = cookies
        self.options = options
        self.dataFB = dataGetHome(cookies)
        
        # Extract user ID from cookies
        cookie_dict = parse_cookie_string(cookies)
        self.user_id = cookie_dict.get("c_user")
        
        if not self.user_id:
            raise Exception("Unable to extract user ID from cookies")
        
        # MQTT context
        self.mqtt_client = None
        self.req_callbacks = {}
        self.req_id_counter = 0
        self.connected = False
        
    def connect(self):
        """Connect to Facebook MQTT server"""
        print(rainbow_text("Connecting to Facebook MQTT..."))
        
        session_id = generate_session_id()
        client_id = generate_client_id()
        
        # User configuration for MQTT
        user_config = {
            "a": self.options["user_agent"],
            "u": self.user_id,
            "s": session_id,
            "chat_on": self.options["online"],
            "fg": False,
            "d": client_id,
            "ct": "websocket",
            "aid": "219994525426954",  # Facebook app ID
            "mqtt_sid": "",
            "cp": 3,
            "ecp": 10,
            "st": [],
            "pm": [],
            "dc": "",
            "no_auto_fg": True,
            "gas": None,
            "pack": [],
        }
        
        # MQTT host
        host = f"wss://edge-chat.facebook.com/chat?sid={session_id}&cid={client_id}"
        
        # Parse cookies for headers
        cookie_dict = parse_cookie_string(self.cookies)
        cookie_str = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])
        
        # MQTT client options
        mqtt_options = {
            "client_id": "mqttwsclient",
            "username": json_minimal(user_config),
            "clean": True,
            "ws_options": {
                "headers": {
                    "Cookie": cookie_str,
                    "Origin": "https://www.facebook.com",
                    "User-Agent": self.options["user_agent"],
                    "Referer": "https://www.facebook.com/",
                    "Host": "edge-chat.facebook.com",
                },
            },
            "keepalive": 10,
        }
        
        # Create MQTT client
        self.mqtt_client = mqtt.Client(
            client_id=mqtt_options["client_id"],
            clean_session=mqtt_options["clean"],
            protocol=mqtt.MQTTv31,
            transport="websockets",
        )
        
        # SSL configuration
        self.mqtt_client.tls_set(
            certfile=None, 
            keyfile=None, 
            cert_reqs=ssl.CERT_NONE, 
            tls_version=ssl.PROTOCOL_TLSv1_2
        )
        self.mqtt_client.tls_insecure_set(True)
        
        # Set callbacks
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_message = self._on_message
        self.mqtt_client.on_disconnect = self._on_disconnect
        
        # Set username
        self.mqtt_client.username_pw_set(username=mqtt_options["username"])
        
        # Parse host for WebSocket options
        parsed_host = urlparse(host)
        self.mqtt_client.ws_set_options(
            path=f"{parsed_host.path}?{parsed_host.query}",
            headers=mqtt_options["ws_options"]["headers"],
        )
        
        # Connect
        self.mqtt_client.connect(
            host=mqtt_options["ws_options"]["headers"]["Host"],
            port=443,
            keepalive=mqtt_options["keepalive"],
        )
        
        # Start loop in background
        self.mqtt_client.loop_start()
        
        # Wait for connection
        timeout = 10
        start_time = time.time()
        while not self.connected and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        if not self.connected:
            raise Exception("Failed to connect to MQTT server")
        
        print(rainbow_text("Connected to Facebook MQTT successfully!"))
    
    def _on_connect(self, client: mqtt.Client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.connected = True
            client.subscribe("/ls_resp", qos=1)
            client.publish(
                topic="/ls_app_settings",
                payload=json_minimal({
                    "ls_fdid": "", 
                    "ls_sv": "6928813347213944"
                }),
                qos=1,
                retain=False,
            )
        else:
            print(f"MQTT Connection failed with code {rc}")
    
    def _on_message(self, client, userdata, msg: mqtt.MQTTMessage):
        """MQTT message callback"""
        if msg.topic == "/ls_resp":
            try:
                payload_str = msg.payload.decode("utf-8")
                parsed = json.loads(payload_str)
                if "request_id" in parsed and parsed["request_id"] in self.req_callbacks:
                    callback = self.req_callbacks[parsed["request_id"]]
                    if "payload" in parsed:
                        response_payload = json.loads(parsed["payload"])
                        if "error" in response_payload:
                            error_msg = response_payload["error"].get("description", "Unknown error")
                            callback(None, error_msg)
                        else:
                            result = {"success": True}
                            callback(result, None)
                    else:
                        callback({"success": True}, None)
                    del self.req_callbacks[parsed["request_id"]]
            except Exception as e:
                pass
    
    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
    
    def share_link(self, url: str, thread_id: str, text: str = "", callback: Optional[Callable] = None):
        if not self.connected:
            raise Exception("MQTT client not connected.")
        
        self.req_id_counter += 1
        request_id = self.req_id_counter
        otid = generate_offline_threading_id()
        
        task_payload = {
            "otid": otid,
            "source": 524289,
            "sync_group": 1,
            "send_type": 6,
            "mark_thread_read": 0,
            "url": url,
            "text": text or "",
            "thread_id": thread_id,
            "initiating_source": 0
        }
        
        task = {
            "label": 46,
            "payload": json_minimal(task_payload),
            "queue_name": thread_id,
            "task_id": random.randint(0, 1000),
            "failure_count": None,
        }
        
        main_payload = {
            "tasks": [task],
            "epoch_id": generate_offline_threading_id(),
            "version_id": "7191105584331330",
        }
        
        message = {
            "app_id": "2220391788200892",
            "payload": json_minimal(main_payload),
            "request_id": request_id,
            "type": 3
        }
        
        if callback:
            self.req_callbacks[request_id] = callback
        
        try:
            result = self.mqtt_client.publish(
                topic="/ls_req",
                payload=json_minimal(message),
                qos=1,
                retain=False,
            )
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except:
            return False

    def disconnect(self):
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            self.connected = False

# --- PHẦN GIAO DIỆN & ĐIỀU KHIỂN ---

def rainbow_text(text, offset=0):
    colors = [(255,0,0), (255,140,0), (255,215,0), (0,255,0), (0,255,200), (0,150,255), (138,43,226), (255,20,147)]
    result = ""
    for i, char in enumerate(text):
        idx = (i + offset * 2) % len(colors)
        r, g, b = colors[idx]
        result += f"\033[38;2;{r};{g};{b}m{char}"
    return result + "\033[0m"

def animate_banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    banner = [
        "┌──────────────────────── INFO ───────────────────────┐",
        " ➜ CHỨC NĂNG: MQTT SHARE LINK SPAMMER 💥",
        " ➜ TRẠNG THÁI: ĐANG HOẠT ĐỘNG",
        "└─────────────────────────────────────────────────────┘",
    ]
    for i in range(20):
        os.system('clear' if os.name == 'posix' else 'cls')
        for line in banner: print(rainbow_text(line, i))
        time.sleep(0.05)

stop_flag = False
current_delay = 1.0

def command_listener():
    global stop_flag, current_delay
    print(rainbow_text("\n[LỆNH ĐIỀU KHIỂN]: 's' để dừng | 'c' để đổi delay\n"))
    while not stop_flag:
        try:
            cmd = input().strip().lower()
            if cmd == 's':
                stop_flag = True
                print(rainbow_text("\n[!] ĐANG DỪNG CHƯƠNG TRÌNH..."))
            elif cmd == 'c':
                new_d = input(rainbow_text("Nhập delay mới (giây): "))
                try:
                    current_delay = float(new_d)
                    print(rainbow_text(f"[OK] Đã cập nhật delay: {current_delay}s"))
                except: print(rainbow_text("[!] Lỗi: Vui lòng nhập số."))
        except EOFError: break

def main():
    global stop_flag, current_delay
    animate_banner()

    # Nhập thông tin thay thế các hàm
    print(rainbow_text("\n--- CẤU HÌNH INPUT ---"))
    cookies_input = input(rainbow_text("Nhập Cookie Facebook: ")).strip()
    thread_id_input = input(rainbow_text("Nhập ID Box (Thread ID): ")).strip()
    url_input = input(rainbow_text("Nhập URL muốn gửi: ")).strip()
    text_input = input(rainbow_text("Nhập Text đi kèm: ")).strip()
    try:
        current_delay = float(input(rainbow_text("Nhập Delay (giây): ")) or "1.0")
    except: current_delay = 1.0

    # Khởi tạo client
    try:
        client = FacebookMQTTShareLink(cookies_input)
        client.connect()
    except Exception as e:
        print(rainbow_text(f"[!] Lỗi khởi tạo: {e}"))
        return

    # Chạy luồng điều khiển
    threading.Thread(target=command_listener, daemon=True).start()

    print(rainbow_text("\n🚀 BẮT ĐẦU SPAM LINK..."))
    count = 0
    
    try:
        while not stop_flag:
            if client.connected:
                success = client.share_link(url_input, thread_id_input, text_input)
                status = "THÀNH CÔNG" if success else "THẤT BẠI"
                count += 1
                ts = time.strftime("%H:%M:%S")
                print(f"\r{rainbow_text(f'[{ts}] Lần {count} | Trạng thái: {status} | Delay: {current_delay}s', count)}", end="")
            else:
                print(rainbow_text("\n[!] Mất kết nối MQTT, đang thử lại..."))
                try: client.connect()
                except: pass
            
            time.sleep(current_delay)
    except KeyboardInterrupt:
        stop_flag = True

    client.disconnect()
    print(rainbow_text("\n\n[✓] Đã dừng và ngắt kết nối."))

if __name__ == "__main__":
    main()

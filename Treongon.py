import requests
import json
import time
import threading
import re
import os
from bs4 import BeautifulSoup

def print_info_banner():
    banner = (              
        "\033[1;39m┌──────────────────────── Info ───────────────────────┐\n"
        "\033[1;33m ➜ \033[1;39mAdmin: YOUNGCE\n"
        "\033[1;33m ➜ \033[1;39mBox: AE HẮC LINH\n"
        "\033[1;33m ➜ \033[1;39mCHỨC NĂNG: LẤY LIST BOX MESSENGER💬\n"
        "\033[1;39m└─────────────────────────────────────────────────────┘\n"
    )
    print(banner)

class Messenger:
    def __init__(self, cookie):
        self.cookie = cookie
        self.user_id = self.get_user_id()
        self.fb_dtsg = None
        self.init_params()

    def get_user_id(self):
        try:
            return re.search(r"c_user=(\d+)", self.cookie).group(1)
        except:
            raise Exception("Cookie không hợp lệ")

    def init_params(self):
        headers = {
            'Cookie': self.cookie,
            'User-Agent': 'Mozilla/5.0'
        }
        try:
            for url in ['https://www.facebook.com', 'https://mbasic.facebook.com', 'https://m.facebook.com']:
                response = requests.get(url, headers=headers)
                match = re.search(r'name="fb_dtsg" value="(.*?)"', response.text)
                if match:
                    self.fb_dtsg = match.group(1)
                    return
            raise Exception("Không tìm thấy fb_dtsg")
        except Exception as e:
            raise Exception(f"Lỗi khởi tạo: {str(e)}")

    def send_message(self, recipient_id, message):
        timestamp = int(time.time() * 1000)
        data = {
            'fb_dtsg': self.fb_dtsg,
            '__user': self.user_id,
            'body': message,
            'action_type': 'ma-type:user-generated-message',
            'timestamp': timestamp,
            'offline_threading_id': str(timestamp),
            'message_id': str(timestamp),
            'thread_fbid': recipient_id,
            'source': 'source:chat:web',
            'client': 'mercury'
        }
        headers = {
            'Cookie': self.cookie,
            'User-Agent': 'Mozilla/5.0',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        try:
            response = requests.post('https://www.facebook.com/messaging/send/', data=data, headers=headers)
            return response.status_code == 200
        except:
            return False

# Biến toàn cục để điều khiển luồng
stop_flag = False
current_delay = 5

def send_messages_loop(messengers, recipient_ids, messages_list):
    global stop_flag, current_delay
    while not stop_flag:
        for recipient_id in recipient_ids:
            if stop_flag: break
            for messenger in messengers:
                if stop_flag: break
                for message in messages_list:
                    if stop_flag: break
                    success = messenger.send_message(recipient_id, message)
                    status = "THÀNH CÔNG" if success else "THẤT BẠI"
                    print(f"\r[{status}] Gửi tới: {recipient_id} | Delay: {current_delay}s", end="")
                    time.sleep(current_delay)

def main():
    global stop_flag, current_delay
    os.system('clear' if os.name == 'posix' else 'cls')
    print_info_banner()

    recipient_ids = []
    print("Nhập ID box (Enter trống hoặc 'done' để kết thúc):")
    while True:
        rid = input("> ").strip()
        if not rid or rid.lower() == 'done': break
        recipient_ids.append(rid)

    cookies = []
    print("\nNhập cookie (Enter trống hoặc 'done' để kết thúc):")
    while True:
        c = input("> ").strip()
        if not c or c.lower() == 'done': break
        cookies.append(c)

    # NHẬP FILE NGÔN GIỐNG NHẬP COOKIE
    messages_list = []
    print("\nNhập tên file ngôn (VD: ngon.txt) (Enter trống hoặc 'done' để kết thúc):")
    while True:
        fn = input("> ").strip()
        if not fn or fn.lower() == 'done': break
        try:
            with open(fn, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    messages_list.append(content)
                    print(f"Đã thêm file: {fn}")
        except:
            print(f"Không đọc được file {fn}, do mày ngu.")

    messengers = []
    for i, cookie in enumerate(cookies, 1):
        try:
            m = Messenger(cookie)
            messengers.append(m)
            print(f"Cookie {i}: OK - User ID: {m.user_id}")
        except Exception as e:
            print(f"Cookie {i}: Lỗi - {e}")

    if not messengers or not messages_list:
        print("Thiếu dữ liệu (Cookie hoặc Nội dung tin nhắn).")
        return

    try:
        current_delay = float(input("\nNhập Delay Vào (giây): "))
    except:
        current_delay = 5

    print("\n💤 Bắt Đầu Spam Ngôn By YOUNGCE🔰💤")
    print("➜ Nhấn 'c' để đổi delay | Nhấn 's' để dừng lại hoàn toàn")

    # Chạy luồng gửi tin nhắn
    thread = threading.Thread(target=send_messages_loop, args=(messengers, recipient_ids, messages_list))
    thread.daemon = True
    thread.start()

    # Vòng lặp lắng nghe lệnh từ bàn phím
    while True:
        cmd = input().lower().strip()
        if cmd == 's':
            stop_flag = True
            print("\n[!] Đang dừng hệ thống...")
            break
        elif cmd == 'c':
            try:
                new_delay = float(input("\nNhập Delay mới: "))
                current_delay = new_delay
                print(f"[OK] Đã đổi delay thành: {current_delay}s")
            except:
                print("[Lỗi] Vui lòng nhập số.")
        
    print("Chương trình kết thúc.")

if __name__ == "__main__":
    main()
  

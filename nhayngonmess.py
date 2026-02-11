import requests
import json
import time
import threading
import re
import os
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
        headers = {'Cookie': self.cookie, 'User-Agent': 'Mozilla/5.0'}
        try:
            for url in ['https://www.facebook.com', 'https://m.facebook.com']:
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

# Biến điều khiển toàn cục
stop_flag = False
current_delay = 5

def nhay_ngon_loop(messengers, recipient_id, name_to_call, lines):
    global stop_flag, current_delay
    while not stop_flag:
        for line in lines:
            if stop_flag: break
            # Thay thế biến {chon_name} bằng tên người cần réo
            formatted_message = line.replace("{chon_name}", name_to_call)
            
            for messenger in messengers:
                if stop_flag: break
                success = messenger.send_message(recipient_id, formatted_message)
                status = "THÀNH CÔNG" if success else "THẤT BẠI"
                print(f"\r[{status}] Gửi tới {recipient_id}: {formatted_message[:30]}... | Delay: {current_delay}s", end="")
                time.sleep(current_delay)

def main():
    global stop_flag, current_delay
    os.system('clear' if os.name == 'posix' else 'cls')
    print_info_banner()

    # 1. Nhập Cookie
    cookies = []
    print("Nhập cookie (Enter trống hoặc 'done' để kết thúc):")
    while True:
        c = input("> ").strip()
        if not c or c.lower() == 'done': break
        cookies.append(c)

    messengers = []
    for i, cookie in enumerate(cookies, 1):
        try:
            m = Messenger(cookie)
            messengers.append(m)
            print(f"Cookie {i}: OK - User ID: {m.user_id}")
        except Exception as e:
            print(f"Cookie {i}: Lỗi - {e}")

    if not messengers:
        print("Không có cookie hợp lệ.")
        return

    # 2. Thông tin mục tiêu
    id_box = input("\nNhập ID Box Messenger: ").strip()
    name_to_call = input("Nhập Họ/Tên người cần réo: ").strip()
    
    try:
        current_delay = float(input("Nhập Delay (giây): "))
    except:
        current_delay = 5

    # 3. Đọc file nhay1.txt
    try:
        with open("nhay1.txt", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        if not lines:
            print("File nhay1.txt không có nội dung!")
            return
    except FileNotFoundError:
        print("Không tìm thấy file nhay1.txt!")
        return

    print(f"\n💤 Bắt đầu nhây ngôn mục tiêu: {name_to_call} 🔰💤")
    print("➜ Nhấn 'c' để đổi delay | Nhấn 's' để dừng lại")

    # Chạy luồng gửi tin nhắn
    thread = threading.Thread(target=nhay_ngon_loop, args=(messengers, id_box, name_to_call, lines))
    thread.daemon = True
    thread.start()

    # Vòng lặp lệnh điều khiển
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

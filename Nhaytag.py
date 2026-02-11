import requests
import json
import time
import threading
import re
import os
import random

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
        self.fb_dtsg = ""
        self.jazoest = ""
        self.init_params()

    def get_user_id(self):
        try:
            return re.search(r"c_user=(\d+)", self.cookie).group(1)
        except:
            raise Exception("Cookie không hợp lệ")

    def init_params(self):
        headers = {'Cookie': self.cookie, 'User-Agent': 'Mozilla/5.0'}
        try:
            response = requests.get('https://m.facebook.com', headers=headers)
            self.fb_dtsg = re.search(r'name="fb_dtsg" value="(.*?)"', response.text).group(1)
            self.jazoest = re.search(r'name="jazoest" value="(.*?)"', response.text).group(1)
        except:
            raise Exception("Không thể lấy fb_dtsg. Kiểm tra lại cookie!")

    def send_tag_message(self, recipient_id, tag_uid, tag_name, message):
        # Cấu trúc nội dung: @Tên Nội_dung
        body = f"@{tag_name} {message}"
        timestamp = int(time.time() * 1000)
        
        # Payload cấu trúc tag (Mention)
        data = {
            'fb_dtsg': self.fb_dtsg,
            'jazoest': self.jazoest,
            'body': body,
            'action_type': 'ma-type:user-generated-message',
            'timestamp': timestamp,
            'offline_threading_id': str(timestamp),
            'message_id': str(timestamp),
            'thread_fbid': recipient_id,
            'source': 'source:chat:web',
            'client': 'mercury',
            'profile_xmd[0][id]': tag_uid,
            'profile_xmd[0][length]': len(tag_name) + 1,
            'profile_xmd[0][offset]': 0,
            'profile_xmd[0][type]': 'p',
        }
        
        headers = {
            'Cookie': self.cookie,
            'User-Agent': 'Mozilla/5.0',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        try:
            res = requests.post('https://www.facebook.com/messaging/send/', data=data, headers=headers)
            return res.status_code == 200
        except:
            return False

# Biến điều khiển
stop_flag = False
current_delay = 5

def nhay_tag_loop(messengers, id_box, target_uids, nhay_lines):
    global stop_flag, current_delay
    
    # Giả lập lấy tên cho các UID (trong tool gốc thường fetch_user_info, ở đây dùng mặc định UID)
    tag_list = [(uid, f"Người dùng {uid}") for uid in target_uids]
    
    while not stop_flag:
        for line in nhay_lines:
            if stop_flag: break
            for messenger in messengers:
                if stop_flag: break
                for uid, name in tag_list:
                    if stop_flag: break
                    
                    success = messenger.send_tag_message(id_box, uid, name, line)
                    status = "THÀNH CÔNG" if success else "THẤT BẠI"
                    
                    print(f"\r[{status}] Tag {uid} tại Box {id_box} | Delay: {current_delay}s", end="")
                    time.sleep(current_delay)

def main():
    global stop_flag, current_delay
    os.system('clear' if os.name == 'posix' else 'cls')
    print_info_banner()

    # 1. Nhập Cookie
    cookies_input = []
    print("Nhập cookie (Enter trống hoặc 'done' để kết thúc):")
    while True:
        c = input("> ").strip()
        if not c or c.lower() == 'done': break
        cookies_input.append(c)

    messengers = []
    for i, ck in enumerate(cookies_input, 1):
        try:
            m = Messenger(ck)
            messengers.append(m)
            print(f"Cookie {i}: OK - User ID: {m.user_id}")
        except Exception as e:
            print(f"Cookie {i}: Lỗi - {e}")

    if not messengers:
        print("Không có cookie hợp lệ.")
        return

    # 2. Nhập ID Box
    id_box = input("\nNhập ID Box Messenger: ").strip()

    # 3. Nhập UID người bị tag
    target_uids = []
    print("\nNhập UID người cần tag (Enter trống hoặc 'done' để kết thúc):")
    while True:
        t_uid = input("> ").strip()
        if not t_uid or t_uid.lower() == 'done': break
        target_uids.append(t_uid)

    if not target_uids:
        print("Chưa nhập UID người bị tag.")
        return

    # 4. Nhập Delay
    try:
        current_delay = float(input("\nNhập Delay (giây): "))
    except:
        current_delay = 2

    # 5. Đọc file nhay.txt
    file_path = "nhay.txt"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            nhay_lines = [l.strip() for l in f if l.strip()]
        if not nhay_lines: raise Exception
    except:
        print(f"Không tìm thấy hoặc file {file_path} trống!")
        return

    print("\n💤 BẮT ĐẦU NHÂY TAG NGÔN BY YOUNGCE HL")
    print("➜ Nhấn 'c' để đổi delay | Nhấn 's' để dừng lại")

    # Chạy luồng gửi tin
    thread = threading.Thread(target=nhay_tag_loop, args=(messengers, id_box, target_uids, nhay_lines))
    thread.daemon = True
    thread.start()

    # Điều khiển lệnh
    while True:
        cmd = input().lower().strip()
        if cmd == 's':
            stop_flag = True
            print("\n[!] Đang dừng hệ thống...")
            break
        elif cmd == 'c':
            try:
                current_delay = float(input("\nNhập Delay mới: "))
                print(f"[OK] Đã đổi delay thành: {current_delay}s")
            except:
                print("[Lỗi] Nhập số.")
        
    print("Chương trình kết thúc.")

if __name__ == "__main__":
    main()
  

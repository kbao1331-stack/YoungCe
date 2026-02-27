import requests
import re
import time
import random
import threading
import os
import math
from datetime import datetime

# --- HỆ THỐNG GIAO DIỆN RAINBOW ---
def rainbow_text(text, offset=0, intensity=1.0):
    result = ""
    t = time.time() * 3 + offset
    for i, char in enumerate(text):
        phase = (i * 0.15 + t) % (math.pi * 2)
        r = int((math.sin(phase) * 127 + 128) * intensity)
        g = int((math.sin(phase + 2) * 127 + 128) * intensity)
        b = int((math.sin(phase + 4) * 127 + 128) * intensity)
        result += f"\033[38;2;{r};{g};{b}m{char}"
    result += "\033[0m"
    return result

def print_rainbow_banner(offset=0):
    lines = [
        "┌──────────────────────── Info ───────────────────────┐",
        " ➜ Admin: YOUNGCE",
        " ➜ Box: AE HẮC LINH",
        " ➜ CHỨC NĂNG: ĐỔI TÊN BOX VÔ HẠN 💥🔥",
        "└─────────────────────────────────────────────────────┘",
    ]
    for line in lines:
        print(rainbow_text(line, offset=offset, intensity=0.9))

def animate_banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    for i in range(40):
        print_rainbow_banner(offset=i * 0.3)
        time.sleep(0.04)
    os.system('clear' if os.name == 'posix' else 'cls')
    print_rainbow_banner(offset=24)

# --- LOGIC XỬ LÝ FACEBOOK (GIỮ NGUYÊN 100%) ---
def parse_cookie_string(cookie_string):
    cookie_dict = {}
    cookies = cookie_string.split(";")
    for cookie in cookies:
        if "=" in cookie:
            key, value = cookie.strip().split("=", 1)
            cookie_dict[key] = value
    return cookie_dict

def Headers(setCookies, dataForm=None, Host="www.facebook.com"):
    headers = {
        "Host": Host,
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Origin": f"https://{Host}",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": f"https://{Host}/",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    if dataForm:
        headers["Content-Length"] = str(len(dataForm))
    return headers

def gen_threading_id():
    return str(
        int(format(int(time.time() * 1000), "b") +
        ("0000000000000000000000" +
        format(int(random.random() * 4294967295), "b"))[-22:], 2)
    )

def dataGetHome(setCookies):
    headers = {
        'Cookie': setCookies,
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
        'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
    }
    dictValueSaved = {}
    try:
        c_user = re.search(r"c_user=(\d+)", setCookies)
        dictValueSaved["FacebookID"] = c_user.group(1) if c_user else "0"
    except:
        dictValueSaved["FacebookID"] = "0"

    response = requests.get("https://www.facebook.com", headers=headers)
    fb_dtsg_match = re.search(r'"token":"(.*?)"', response.text)
    if not fb_dtsg_match:
        fb_dtsg_match = re.search(r'name="fb_dtsg" value="(.*?)"', response.text)
    dictValueSaved["fb_dtsg"] = fb_dtsg_match.group(1) if fb_dtsg_match else ""
    jazoest_match = re.search(r'jazoest=(\d+)', response.text)
    if not jazoest_match:
        jazoest_match = re.search(r'name="jazoest" value="(\d+)"', response.text)
    dictValueSaved["jazoest"] = jazoest_match.group(1) if jazoest_match else "22036"
    dictValueSaved["clientRevision"] = "999999999"
    dictValueSaved["cookieFacebook"] = setCookies
    return dictValueSaved

def tenbox(newTitle, threadID, dataFB):
    try:
        message_id = gen_threading_id()
        timestamp = int(time.time() * 1000)
        form_data = {
            "client": "mercury",
            "action_type": "ma-type:log-message",
            "author": f"fbid:{dataFB['FacebookID']}",
            "thread_id": str(threadID),
            "timestamp": timestamp,
            "timestamp_relative": str(int(time.time())),
            "source": "source:chat:web",
            "source_tags[0]": "source:chat",
            "offline_threading_id": message_id,
            "message_id": message_id,
            "threading_id": gen_threading_id(),
            "thread_fbid": str(threadID),
            "thread_name": str(newTitle),
            "log_message_type": "log:thread-name",
            "fb_dtsg": dataFB["fb_dtsg"],
            "jazoest": dataFB["jazoest"],
            "__user": str(dataFB["FacebookID"]),
            "__a": "1",
            "__req": "1",
            "__rev": dataFB.get("clientRevision", "1015919737")
        }
        response = requests.post(
            "https://www.facebook.com/messaging/set_thread_name/",
            data=form_data,
            headers=Headers(dataFB["cookieFacebook"], form_data),
            cookies=parse_cookie_string(dataFB["cookieFacebook"]),
            timeout=10
        )
        if response.status_code == 200:
            return True, f"✅ [{datetime.now().strftime('%H:%M:%S')}] Đã đổi tên thành: {newTitle}"
        else:
            return False, f"❌ [{datetime.now().strftime('%H:%M:%S')}] Lỗi HTTP {response.status_code}"
    except Exception as e:
        return False, f"❌ [{datetime.now().strftime('%H:%M:%S')}] Lỗi: {e}"

# --- HỆ THỐNG ĐIỀU KHIỂN ---
stop_flag = False
current_delay = 1.0

def run_loop(lines, thread_id, dataFB):
    global stop_flag, current_delay
    counter = 0
    while not stop_flag:
        for line in lines:
            if stop_flag: break
            counter += 1
            success, log_msg = tenbox(line, thread_id, dataFB)
            
            # In Log với hiệu ứng Rainbow
            full_log = f"{log_msg} | Lần: {counter} | Delay: {current_delay}s"
            print(f"\n{rainbow_text(full_log, offset=time.time()*5, intensity=0.95)}", end="")
            
            # Delay có khả năng ngắt (Interruptible Sleep)
            end_sleep = time.time() + current_delay
            while time.time() < end_sleep and not stop_flag:
                time.sleep(0.1)

def main():
    global stop_flag, current_delay
    animate_banner()

    # Nhập thông tin cấu hình
    print(rainbow_text("--- CẤU HÌNH TOOL ĐỔI TÊN ---", intensity=0.8))
    cookie = input(rainbow_text("🔐 Nhập cookie Facebook: ", intensity=0.7)).strip()
    thread_id = input(rainbow_text("💬 Nhập ID nhóm (thread_fbid): ", intensity=0.7)).strip()
    
    file_path = input(rainbow_text("📂 Nhập tên file nội dung (vd: nhay.txt): ", intensity=0.7)).strip() or "nhay.txt"
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        if not lines: raise Exception
    except:
        print(rainbow_text(f"❌ Không tìm thấy hoặc file {file_path} trống!", intensity=0.8))
        return

    try:
        current_delay = float(input(rainbow_text("⏱️ Nhập delay (giây): ", intensity=0.7)) or "1.0")
    except:
        current_delay = 1.0

    # Lấy thông tin FB
    print(rainbow_text("\n🔄 Đang kiểm tra Cookie và lấy Token...", intensity=0.8))
    dataFB = dataGetHome(cookie)
    
    if dataFB["fb_dtsg"] == "":
        print(rainbow_text("❌ Cookie lỗi hoặc không lấy được fb_dtsg!", intensity=0.8))
        return

    print(rainbow_text(f"✅ Đã nhận diện User ID: {dataFB['FacebookID']}", intensity=0.9))
    print(rainbow_text("\n💥 BẮT ĐẦU CHẠY VÔ HẠN 🔥🌈", intensity=1.0))
    print(rainbow_text("➜ 's' = Dừng | 'c' = Đổi delay nhanh"))

    # Chạy thread chính
    t = threading.Thread(target=run_loop, args=(lines, thread_id, dataFB))
    t.daemon = True
    t.start()

    # Lắng nghe lệnh điều khiển
    while True:
        cmd = input().strip().lower()
        if cmd == 's':
            stop_flag = True
            print(rainbow_text("\n[!] ĐANG DỪNG... Vui lòng chờ giây lát.", intensity=0.9))
            break
        elif cmd == 'c':
            try:
                new_d = float(input(rainbow_text("Delay mới (giây): ", intensity=0.8)))
                current_delay = max(0.1, new_d)
                print(rainbow_text(f"[OK] Đã cập nhật delay: {current_delay}s", intensity=0.95))
            except:
                print(rainbow_text("[Lỗi] Nhập số không hợp lệ!", intensity=0.7))

    print(rainbow_text("Tool đã dừng hẳn. 🌈"))
    time.sleep(1)

if __name__ == "__main__":
    main()

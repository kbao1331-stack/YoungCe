import requests
from bs4 import BeautifulSoup
import time
import threading
import os

# --- CẤU HÌNH & BIẾN TOÀN CỤC ---
stop_flag = False
pause_flag = False
email_history = []  
current_index = -1  
seen_messages = set() 

# --- GIAO DIỆN RAINBOW ---
def rainbow_text(text, offset=0):
    colors = [(255, 0, 0), (255, 140, 0), (255, 215, 0), (0, 255, 0),
              (0, 255, 200), (0, 150, 255), (138, 43, 226), (255, 20, 147)]
    result = ""
    for i, char in enumerate(text):
        idx = (i + offset * 2) % len(colors)
        r, g, b = colors[idx]
        result += f"\033[38;2;{r};{g};{b}m{char}"
    return result + "\033[0m"

def print_banner(offset=0):
    lines = [
        "┌──────────────────────── INFO ───────────────────────┐",
        " ➜ Admin: YOUNGCE | Tool: TEMP MAIL MANAGER",
        " ➜ Lệnh: [c] Đổi Mail | [t] Mail Trước | [r] Làm mới",
        " ➜ Lệnh: [s] Thoát chương trình",
        "└─────────────────────────────────────────────────────┘",
    ]
    for line in lines: print(rainbow_text(line, offset))

# --- CHỨC NĂNG CORE (MAIL) ---
def get_new_email():
    url = "https://10minutemail.net/?lang=vi"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        session = requests.Session()
        res = session.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            email_input = soup.find("input", {"id": "fe_text"})
            if email_input:
                return email_input["value"], session.cookies.get_dict()
    except: pass
    return None, None

def check_mailbox(email, cookies, manual=False):
    global seen_messages
    url = "https://10minutemail.net/mailbox.ajax.php"
    headers = {"User-Agent": "Mozilla/5.0"}
    if manual:
        print(rainbow_text(f"\n[*] Đang làm mới hộp thư cho: {email}...", 5))
    
    try:
        session = requests.Session()
        session.cookies.update(cookies)
        res = session.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            mails = soup.find_all("tr", style=lambda v: v and "cursor: pointer" in v)
            found_new = False
            for mail in mails:
                links = mail.find_all("a", class_="row-link")
                if len(links) >= 2:
                    sender = links[0].text.strip()
                    subject = links[1].text.strip()
                    msg_id = f"{sender}|{subject}"
                    if msg_id not in seen_messages:
                        seen_messages.add(msg_id)
                        ts = time.strftime("%H:%M:%S")
                        print(f"{rainbow_text(f'[{ts}] 📩 MỚI | Từ: {sender} | Nội dung: {subject}', 10)}")
                        found_new = True
            if manual and not found_new:
                print(rainbow_text("[!] Không có thư mới.", 0))
    except:
        if manual: print(rainbow_text("[X] Lỗi kết nối khi làm mới!", 0))

# --- ĐIỀU KHIỂN LUỒNG ---
def command_listener():
    global stop_flag, email_history, current_index, pause_flag
    while not stop_flag:
        try:
            cmd = input().strip().lower()
            if cmd == 's':
                stop_flag = True
                break
            elif cmd == 'c':
                pause_flag = True
                print(rainbow_text("\n[+] Đang lấy email mới...", 5))
                new_e, new_c = get_new_email()
                if new_e:
                    email_history.append((new_e, new_c))
                    current_index = len(email_history) - 1
                    print(rainbow_text(f"➜ Email hiện tại: {new_e}", 20))
                pause_flag = False
            elif cmd == 't':
                if current_index > 0:
                    current_index -= 1
                    e, _ = email_history[current_index]
                    print(rainbow_text(f"\n[←] Quay lại email ({current_index + 1}/{len(email_history)}): {e}", 15))
                else:
                    print(rainbow_text("\n[!] Đã ở email đầu tiên!", 0))
            elif cmd == 'r':
                if current_index != -1:
                    e, c = email_history[current_index]
                    check_mailbox(e, c, manual=True)
        except EOFError: break

def main():
    global stop_flag, email_history, current_index, pause_flag
    os.system('clear' if os.name == 'posix' else 'cls')
    print_banner(25)
    
    print(rainbow_text("Đang khởi tạo ứng dụng...", 10))
    e, c = get_new_email()
    if e:
        email_history.append((e, c))
        current_index = 0
        print(rainbow_text(f"Email mặc định: {e}", 20))
        print(rainbow_text("Gõ lệnh: c (đổi), t (lùi), r (làm mới), s (thoát)\n", 10))
    
    threading.Thread(target=command_listener, daemon=True).start()

    try:
        while not stop_flag:
            if not pause_flag and current_index != -1:
                curr_mail, curr_cookie = email_history[current_index]
                # Tự động quét ngầm mỗi 10 giây (vẫn giữ để mail không chết)
                check_mailbox(curr_mail, curr_cookie, manual=False)
            
            time.sleep(10)
    except KeyboardInterrupt:
        stop_flag = True

    print(rainbow_text("\nChương trình đã dừng. Tạm biệt!", 0))

if __name__ == "__main__":
    main()

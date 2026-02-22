import asyncio
import aiohttp
import time
import threading
import os
import re

# --- GIAO DIỆN & HIỆU ỨNG RAINBOW ---

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
        " ➜ CHỨC NĂNG: DISCORD SPAMMER PRO 💥",
        "└─────────────────────────────────────────────────────┘",
    ]
    for line in lines:
        print(rainbow_text(line, offset=offset))

def animate_banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    for i in range(25):
        print_rainbow_banner(offset=i)
        time.sleep(0.04)
    os.system('clear' if os.name == 'posix' else 'cls')
    print_rainbow_banner(offset=25)

# --- BIẾN ĐIỀU KHIỂN TOÀN CỤC ---

stop_flag = False
pause_flag = False
current_delay = 0.3
messages_list = []

# --- HÀM XỬ LÝ DISCORD (ASYNCHRONOUS) ---

async def _discord_spam_worker(session, token, channels, message, delay):
    global stop_flag, pause_flag
    headers = {
        "Authorization": token.strip(),
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "X-Super-Properties": "eyJvcyI6IldpbmRvd3MiLCJjbGllbnRfdmVyc2lvbiI6IjEwMC4wLjAuMCJ9"
    }
    
    while not stop_flag:
        if pause_flag:
            await asyncio.sleep(0.5)
            continue

        for channel_id in channels:
            if stop_flag: break
            
            # Cắt tin nhắn nếu quá giới hạn Discord
            content = message[:2000] if len(message) > 2000 else message
            data = {"content": content}
            url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
            
            try:
                async with session.post(url, headers=headers, json=data) as resp:
                    status = resp.status
                    ts = time.strftime("%H:%M:%S")
                    if status in [200, 201]:
                        print(f"\r{rainbow_text(f'[✓] {ts} | Token: {token[:10]}... | Gửi Channel: {channel_id} | OK')}", end="")
                    elif status in [401, 403]:
                        print(f"\n{rainbow_text(f'[×] Token DIE/Lỗi Quyền: {token[:15]}... | Status: {status}')}")
                        return # Dừng worker này nếu token lỗi
                    elif status == 429: # Rate limit
                        retry_after = (await resp.json()).get('retry_after', 5)
                        await asyncio.sleep(retry_after)
                    else:
                        print(f"\n{rainbow_text(f'[×] Lỗi {status} tại Channel {channel_id}')}")
            except Exception as e:
                print(f"\n[!] Ngoại lệ: {e}")
            
            await asyncio.sleep(delay)

# --- HỆ THỐNG LẮNG NGHE LỆNH ---

def command_listener():
    global stop_flag, pause_flag, current_delay
    while not stop_flag:
        try:
            cmd = input().strip().lower()
            if cmd == 's':
                stop_flag = True
                print(rainbow_text("\n[!] ĐANG DỪNG HỆ THỐNG..."))
                break
            elif cmd == 'c':
                pause_flag = True
                try:
                    new_d = float(input(rainbow_text("Nhập delay mới (giây): ")))
                    current_delay = max(0.01, new_d)
                    print(rainbow_text(f"[OK] Đã đổi delay thành: {current_delay}s"))
                except: print(rainbow_text("[Lỗi] Định dạng số sai"))
                pause_flag = False
            # Bạn có thể thêm lệnh 'f' để đổi nội dung ở đây
        except: pass

# --- LUỒNG CHÍNH ---

async def start_spam(tokens, channels, delay, message):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for token in tokens:
            tasks.append(_discord_spam_worker(session, token, channels, message, delay))
        await asyncio.gather(*tasks)

def main():
    global current_delay, stop_flag
    animate_banner()

    # Nhập ID Channel
    channels = []
    print(rainbow_text("Nhập danh sách ID Channel (Xong gõ 'done'):"))
    while True:
        cid = input(rainbow_text("> ")).strip()
        if not cid or cid.lower() == 'done': break
        channels.append(cid)

    # Nhập Token Discord
    tokens = []
    print(rainbow_text("\nNhập danh sách Token Discord (Xong gõ 'done'):"))
    while True:
        tkn = input(rainbow_text("> ")).strip()
        if not tkn or tkn.lower() == 'done': break
        tokens.append(tkn)

    # Nhập nội dung (Load từ file hoặc nhập trực tiếp)
    print(rainbow_text("\nNhập nội dung tin nhắn (Hoặc tên file .txt):"))
    msg_input = input(rainbow_text("> ")).strip()
    if os.path.exists(msg_input):
        with open(msg_input, 'r', encoding='utf-8') as f:
            message = f.read()
    else:
        message = msg_input

    # Nhập Delay
    try:
        delay_val = input(rainbow_text("\nNhập delay (mặc định 0.3): ") or "0.3")
        current_delay = float(delay_val)
    except:
        current_delay = 0.3

    if not tokens or not channels:
        print(rainbow_text("\n[!] Thiếu Token hoặc Channel ID → Thoát"))
        return

    print(rainbow_text("\n💥 DISCORD SPAM ĐÃ BẮT ĐẦU – By YOUNGCE 🔥"))
    print(rainbow_text("Lệnh: s (Dừng) | c (Đổi delay)\n"))

    # Khởi chạy thread lắng nghe lệnh
    threading.Thread(target=command_listener, daemon=True).start()

    # Chạy vòng lặp Async
    try:
        asyncio.run(start_spam(tokens, channels, current_delay, message))
    except KeyboardInterrupt:
        stop_flag = True

    print(rainbow_text("\nChương trình đã kết thúc."))

if __name__ == "__main__":
    main()

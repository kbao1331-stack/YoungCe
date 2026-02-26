import os
import sys
import requests
from time import sleep
import math
import time

# Màu sắc rainbow gradient mượt (sin wave)
def rainbow_text(text, offset=0, intensity=0.95):
    result = ""
    t = time.time() * 4 + offset  # tốc độ chạy ngang nhanh, đẹp
    for i, char in enumerate(text):
        phase = (i * 0.18 + t) % (math.pi * 2)
        r = int((math.sin(phase) * 127 + 128) * intensity)
        g = int((math.sin(phase + 2.094) * 127 + 128) * intensity)  # phase shift cho gradient đẹp
        b = int((math.sin(phase + 4.188) * 127 + 128) * intensity)
        result += f"\033[38;2;{r};{g};{b}m{char}"
    result += "\033[0m"
    return result

# Clear screen
os.system("cls" if os.name == "nt" else "clear")

# Banner rainbow
banner = f"""
{rainbow_text("╔═══════════════════════════════════════════════╗")}
{rainbow_text("║                YOUNGCE                           ║                 HẮC LINH")}
{rainbow_text("╚═══════════════════════════════════════════════╝")}

{rainbow_text("👑 Tool by: YOUNG CE HAC LINH")}
{rainbow_text("📱 FACEBOOK: https://www.facebook.com/profile.php?id=61586387813367")}
{rainbow_text("⚡ Tool: YoungCe MESSENGER")}
"""

print(banner)

# Menu rainbow
menu = f"""
{rainbow_text("┌────────────────────────────────────────────────┐")}
{rainbow_text("│             CHỨC NĂNG DiSCORD(DEMO)              │")}
{rainbow_text("├────────────────────────────────────────────────┤")}
{rainbow_text("[7] TREO DIS ")}
{rainbow_text("┌────────────────────────────────────────────────┐")}
{rainbow_text("│             CHỨC NĂNG GMAIL              │")}
{rainbow_text("├────────────────────────────────────────────────┤")}
{rainbow_text("[8] MAIL ẢO ")}
{rainbow_text("┌────────────────────────────────────────────────┐")}
{rainbow_text("│             CHỨC NĂNG MESSENGER              │")}
{rainbow_text("├────────────────────────────────────────────────┤")}
{rainbow_text("[1] TREO NGÔN BẤT TỬ ")}
{rainbow_text("[2] NHÂY MESS ")}
{rainbow_text("[3] NHÂY TAG ")}
{rainbow_text("[4] LẤY LIST BOX ")}
{rainbow_text("[5] NHÂY POLL MESS ")}
{rainbow_text("[6] SET NỀN LIÊN TỤC ")}
{rainbow_text("[0] THOÁT TOOL ")}
{rainbow_text("└────────────────────────────────────────────────┘")}
"""

print(menu)

# Chọn chức năng
try:
    chon_input = input(rainbow_text("➩ Chọn chức năng: ", intensity=0.9))
    chon = int(chon_input)
    
    url_map = {
        7: 'https://raw.githubusercontent.com/kbao1331-stack/YoungCe/refs/heads/main/treodis.py',
        8: 'https://raw.githubusercontent.com/kbao1331-stack/YoungCe/refs/heads/main/mailao.py',
        1: 'https://raw.githubusercontent.com/kbao1331-stack/YoungCe2/refs/heads/main/treongon_lite.py',
        2: 'https://raw.githubusercontent.com/kbao1331-stack/YoungCe2/refs/heads/main/nhayngonmess.py',
        3: 'https://raw.githubusercontent.com/kbao1331-stack/YoungCe2/refs/heads/main/nhaytagmess.py',
        5: 'https://raw.githubusercontent.com/kbao1331-stack/YoungCe/refs/heads/main/nhaypoll.py,
        6: 'https://raw.githubusercontent.com/kbao1331-stack/YoungCe/refs/heads/main/treonen.py',
        4: 'https://raw.githubusercontent.com/kbao1331-stack/YoungCe2/refs/heads/main/listbox.py'
    }
    
    if chon in url_map:
        print(rainbow_text(f"Đang tải và chạy chức năng {chon}...", intensity=0.85))
        sleep(0.8)  # delay nhẹ cho cảm giác mượt
        exec(requests.get(url_map[chon]).text)
    elif chon == 0:
        print(rainbow_text("[YOUNGCE TOOL] Thoát tool thành công.", intensity=0.9))
        exit()
    else:
        print(rainbow_text("[LỖI] Lựa chọn không hợp lệ!", intensity=0.7))
        
except ValueError:
    print(rainbow_text("[LỖI] Vui lòng nhập số!", intensity=0.7))
except KeyboardInterrupt:
    print(rainbow_text("\n[YoungCe TOOL] Thoát tool thành công.", intensity=0.9))
    exit()
except Exception as e:
    print(rainbow_text(f"[LỖI] Có lỗi xảy ra: {str(e)}", intensity=0.7))
import requests
import json
import time
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
            # Giữ nguyên logic regex lấy ID từ cookie của file treongondo.py
            return re.search(r"c_user=(\d+)", self.cookie).group(1)
        except:
            raise Exception("Cookie không hợp lệ")

    def init_params(self):
        headers = {
            'Cookie': self.cookie,
            'User-Agent': 'Mozilla/5.0'
        }
        try:
            # Giữ nguyên logic lấy fb_dtsg bằng cách duyệt qua các domain
            for url in ['https://www.facebook.com', 'https://mbasic.facebook.com', 'https://m.facebook.com']:
                response = requests.get(url, headers=headers)
                match = re.search(r'name="fb_dtsg" value="(.*?)"', response.text)
                if match:
                    self.fb_dtsg = match.group(1)
                    return
            raise Exception("Không tìm thấy fb_dtsg")
        except Exception as e:
            raise Exception(f"Lỗi khởi tạo: {str(e)}")

    def get_thread_list(self, limit=50):
        # Logic lấy danh sách box từ file treotruvbach.py
        headers = {
            'Cookie': self.cookie,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-FB-Friendly-Name': 'MessengerThreadListQuery',
        }
        form_data = {
            "av": self.user_id,
            "__user": self.user_id,
            "__a": "1",
            "fb_dtsg": self.fb_dtsg,
            "queries": json.dumps({
                "o0": {
                    "doc_id": "3336396659757871",
                    "query_params": {
                        "limit": limit,
                        "before": None,
                        "tags": ["INBOX"],
                        "includeDeliveryReceipts": False,
                        "includeSeqID": True,
                    }
                }
            })
        }
        try:
            response = requests.post('https://www.facebook.com/api/graphqlbatch/', data=form_data, headers=headers)
            response_text = response.text.split('{"successful_results"')[0]
            data = json.loads(response_text)
            threads = data["o0"]["data"]["viewer"]["message_threads"]["nodes"]
            return threads
        except:
            return []

def main():
    os.system('clear' if os.name == 'posix' else 'cls')
    print_info_banner()

    # Khôi phục logic nhập Cookie cũ từ treongondo.py
    cookies = []
    print("\nNhập cookie (Enter trống hoặc 'done' để kết thúc):")
    while True:
        c = input("> ").strip()
        if not c or c.lower() == 'done': break
        cookies.append(c)

    if not cookies:
        print("Thiếu dữ liệu Cookie.")
        return

    # Duyệt qua từng cookie và lấy list box
    for i, cookie in enumerate(cookies, 1):
        try:
            m = Messenger(cookie)
            print(f"\nCookie {i}: OK - User ID: {m.user_id}")
            print("--- Danh sách Box ---")
            
            threads = m.get_thread_list()
            if not threads:
                print("Không tìm thấy dữ liệu box.")
                continue

            for idx, thread in enumerate(threads, 1):
                t_id = thread["thread_key"]["thread_fbid"]
                t_name = thread.get("name", "Chat riêng/Không tên")
                print(f"{idx}. {t_name} | ID: {t_id}")
                
        except Exception as e:
            print(f"Cookie {i}: Lỗi - {e}")

    print("\nChương trình kết thúc.")

if __name__ == "__main__":
    main()

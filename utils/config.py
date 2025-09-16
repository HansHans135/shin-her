import json
import os

from cryptography.fernet import Fernet

def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not data['app']['secret_key']:
        data['app']['secret_key'] = Fernet.generate_key().decode
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            print("已生成新的 API secret_key 並保存到 config.json")

    if not os.path.isfile('data/api/key.json'):
        os.makedirs('data/api', exist_ok=True)
        with open('data/api/key.json', 'w+', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
        print("已生成 data/api/key.json 檔案")
    if not os.path.isfile('data/api/token.json'):
        with open('data/api/token.json', 'w+', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
        print("已生成 data/api/token.json 檔案")
    return data

config = load_config()

def load_cookies_from_file(account):
    try:
        cookie_file_path = f'data/cookie/{account}.json'
        if os.path.exists(cookie_file_path):
            with open(cookie_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"載入 cookies 檔案時發生錯誤: {e}")
    return None

def get_headers(account):
    if not account:
        return None
    
    cookies = load_cookies_from_file(account)
    if not cookies:
        return None
    
    headers = {
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "zh-TW,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "cache-control": "no-cache",
        "cookie": "; ".join([f"{k}={v}" for k, v in cookies.items()]),
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0"
    }
    return headers
import requests
import json
import os
from datetime import datetime
from urllib.parse import urlparse

def load_config():
    """載入設定檔"""
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

config = load_config()

def load_cookies_from_file(filename="login_cookies.json"):
    """從 JSON 檔案載入 cookies"""
    try:
        if not os.path.exists(filename):
            print(f"Cookie 檔案不存在: {filename}")
            return None
            
        with open(filename, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        print(f"已載入 {len(cookies)} 個 cookies")
        return cookies
    except Exception as e:
        print(f"載入 cookies 時發生錯誤: {e}")
        return None

def save_updated_cookies(session, filename):
    """保存更新後的 cookies"""
    try:
        cookie_dict = {cookie.name: cookie.value for cookie in session.cookies}
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cookie_dict, f, indent=2, ensure_ascii=False)
        print(f"已保存更新後的 cookies 到: {filename}")
        return cookie_dict
    except Exception as e:
        print(f"保存更新後的 cookies 時發生錯誤: {e}")
        return None

def fetch_page_data(url, cookies_file, save_html=True, visit_root=False):
    """使用 requests 獲取頁面資料"""
    
    try:
        print(f"=== 開始獲取頁面資料 (Requests版本) ===")
        print(f"目標 URL: {url}")
        
        # 載入 cookies
        cookies = load_cookies_from_file(cookies_file)
        if not cookies:
            print("無法載入 cookies，請先執行登入程式")
            return None
        
        # 建立 session
        session = requests.Session()
        
        # 設定 headers
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # 添加 cookies 到 session
        for name, value in cookies.items():
            session.cookies.set(name, value)
        
        # 如果需要先訪問 root
        if visit_root:
            base_url = config['school']['root_url']
            print(f"正在訪問 root: {base_url}")
            root_response = session.get(base_url, allow_redirects=True, timeout=30)
            print(f"Root 訪問狀態碼: {root_response.status_code}")
        else:
            print("跳過訪問 root，直接前往目標頁面")
        
        # 訪問目標頁面
        print(f"正在訪問目標頁面: {url}")
        response = session.get(url, allow_redirects=True, timeout=30)
        
        # 檢查回應
        print(f"\n=== 頁面資訊 ===")
        print(f"狀態碼: {response.status_code}")
        print(f"最終 URL: {response.url}")
        print(f"編碼: {response.encoding}")
        print(f"頁面大小: {len(response.text)} 字元")
        
        # 檢查是否被重定向到登入頁面
        if "auth/online" in response.url or response.status_code == 401:
            print("可能需要重新登入，頁面被重定向到登入頁面")
        else:
            print("成功訪問頁面")
        
        # 保存 HTML
        if save_html:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"page_data_requests_{timestamp}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"已保存 HTML 到: {filename}")
        
        # 簡單的內容分析
        print(f"\n=== 頁面內容分析 ===")
        content = response.text.lower()
        print(f"包含 'table' 標籤: {'是' if '<table' in content else '否'}")
        print(f"包含 'form' 標籤: {'是' if '<form' in content else '否'}")
        print(f"包含 'input' 標籤: {'是' if '<input' in content else '否'}")
        
        # 保存更新的 cookies
        updated_cookies = save_updated_cookies(session, cookies_file)
        
        # 整理回傳資料
        page_data = {
            'url': response.url,
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'html': response.text,
            'cookies': updated_cookies,
            'timestamp': datetime.now().isoformat()
        }
        
        return page_data
        
    except requests.exceptions.Timeout:
        print(f"請求超時")
        return None
    except requests.exceptions.ConnectionError:
        print(f"連線錯誤")
        return None
    except requests.exceptions.RequestException as e:
        print(f"獲取頁面資料時發生錯誤: {e}")
        return None
    except Exception as e:
        print(f"未預期的錯誤: {e}")
        return None

def get_page_data(url, cookies_file, save_html=True, visit_root=False):
    """
    獲取頁面資料的主要函數 (Requests 版本)
    
    Args:
        url (str): 要訪問的網址
        cookies_file (str): 要使用的 cookies JSON 檔案路徑
        save_html (bool): 是否保存 HTML 檔案
        visit_root (bool): 是否先訪問 root URL
    
    Returns:
        dict: 包含頁面資料的字典，失敗時返回 None
    """
    if not os.path.exists(cookies_file):
        print(f"Cookie 檔案不存在: {cookies_file}")
        return None
    
    print(f"目標 URL: {url}")
    print(f"Cookies 檔案: {cookies_file}")
    
    result = fetch_page_data(url, cookies_file, save_html, visit_root)
    
    if result:
        print(f"\n成功獲取頁面資料!")
        print(f"頁面統計:")
        print(f"   - 狀態碼: {result['status_code']}")
        print(f"   - URL: {result['url']}")
        print(f"   - HTML 大小: {len(result['html'])} 字元")
        print(f"   - Cookies 數量: {len(result['cookies']) if result['cookies'] else 0}")
        print(f"   - 獲取時間: {result['timestamp']}")
    else:
        print(f"獲取頁面資料失敗")
    
    return result

# 使用範例
if __name__ == "__main__":
    # 範例用法
    test_url = "https://ykvs.ntpc.edu.tw/p/412-1000-1491.php"
    cookies_file = "login_cookies.json"
    
    result = get_page_data(
        url=test_url,
        cookies_file=cookies_file,
        save_html=True,
        visit_root=False
    )
    
    if result:
        print("\n✓ 成功獲取頁面")
    else:
        print("\n✗ 獲取失敗")

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import os
from datetime import datetime

def setup_driver():
    """設定 Chrome WebDriver"""
    chrome_options = Options()
    
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument('--ignore-certificate-errors')

    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument('--ignore-certificate-errors-spki-list') 
    chrome_options.add_argument('--disable-extensions-http-throttling')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-urlfetcher-cert-requests')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--remote-debugging-port=9223')
    
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    stealth_js = """
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    Object.defineProperty(navigator, 'languages', {get: () => ['zh-TW', 'zh', 'en']});
    window.chrome = {runtime: {}};
    Object.defineProperty(navigator, 'permissions', {get: () => ({query: () => Promise.resolve({state: 'granted'})})});
    """
    driver.execute_script(stealth_js)
    
    return driver

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

def add_cookies_to_driver(driver, cookies):
    """將 cookies 添加到 WebDriver"""
    try:
        if isinstance(cookies, dict):
            cookie_list = []
            for name, value in cookies.items():
                cookie_dict = {
                    'name': name,
                    'value': str(value),
                    'domain': '.ykvs.ntpc.edu.tw',
                    'path': '/'
                }
                cookie_list.append(cookie_dict)
            cookies = cookie_list
        elif isinstance(cookies, list):
            pass
        else:
            print(f"不支援的 cookies 格式: {type(cookies)}")
            return False
        
        for cookie in cookies:
            clean_cookie = {
                'name': cookie['name'],
                'value': cookie['value'],
                'domain': cookie.get('domain', '.ykvs.ntpc.edu.tw'),
                'path': cookie.get('path', '/')
            }
            
            if 'secure' in cookie:
                clean_cookie['secure'] = cookie['secure']
            if 'httpOnly' in cookie:
                clean_cookie['httpOnly'] = cookie['httpOnly']
            if 'expiry' in cookie:
                clean_cookie['expiry'] = int(cookie['expiry'])
                
            driver.add_cookie(clean_cookie)
        
        print(f"已添加 {len(cookies)} 個 cookies 到瀏覽器")
        return True
    except Exception as e:
        print(f"添加 cookies 時發生錯誤: {e}")
        return False

def save_updated_cookies(driver, filename):
    try:
        cookies = driver.get_cookies()
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cookie_dict, f, indent=2, ensure_ascii=False)
        print(f"已保存更新後的 cookies 到: {filename}")
        return cookie_dict
    except Exception as e:
        print(f"保存更新後的 cookies 時發生錯誤: {e}")
        return None

def fetch_page_data(url, cookies_file, save_html=True):
    driver = setup_driver()
    
    try:
        print(f"=== 開始獲取頁面資料 ===")
        print(f"目標 URL: {url}")
        
        cookies = load_cookies_from_file(cookies_file)
        if not cookies:
            print("無法載入 cookies，請先執行登入程式")
            return None
        
        base_url = "https://eschool.ykvs.ntpc.edu.tw/"
        print(f"正在訪問root: {base_url}")
        driver.get(base_url)

        if not add_cookies_to_driver(driver, cookies):
            print("無法設置 cookies")
            return None
        
        print(f"正在訪問目標頁面: {url}")
        driver.get(url)
        
        WebDriverWait(driver, 10).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        
        current_url = driver.current_url
        page_title = driver.title
        page_source = driver.page_source
        
        print(f"\n=== 頁面資訊 ===")
        print(f"當前 URL: {current_url}")
        print(f"頁面標題: {page_title}")
        print(f"頁面大小: {len(page_source)} 字元")
        
        if "auth/online" in current_url or "登入" in page_title:
            print("可能需要重新登入，頁面被重定向到登入頁面")
        else:
            print("成功訪問頁面")
        
        if save_html:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"page_data_{timestamp}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(page_source)
            print(f"{filename}")
        
        try:
            print(f"\n=== 頁面內容分析 ===")
            
            tables = driver.find_elements(By.TAG_NAME, "table")
            if tables:
                print(f"找到 {len(tables)} 個表格")
                for i, table in enumerate(tables, 1):
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    print(f"表格 {i}: {len(rows)} 行")
            
            forms = driver.find_elements(By.TAG_NAME, "form")
            if forms:
                print(f"找到 {len(forms)} 個表單")
            
            important_elements = []
            for selector in ["input", "select", "textarea", "button"]:
                elements = driver.find_elements(By.TAG_NAME, selector)
                if elements:
                    important_elements.append(f"{selector}: {len(elements)} 個")
            
            if important_elements:
                print(f"頁面元素: {', '.join(important_elements)}")
                
        except Exception as e:
            print(f"分析頁面內容時發生錯誤: {e}")
        
        updated_cookies = save_updated_cookies(driver, cookies_file)
        
        page_data = {
            'url': current_url,
            'title': page_title,
            'html': page_source,
            'cookies': updated_cookies,
            'timestamp': datetime.now().isoformat()
        }
        
        return page_data
        
    except Exception as e:
        print(f"獲取頁面資料時發生錯誤: {e}")
        return None
    
    finally:
        driver.quit()
        print("瀏覽器已關閉")

def get_page_data(url, cookies_file, save_html=True):
    """
    獲取頁面資料的主要函數 - 透過參數傳入
    
    Args:
        url (str): 要訪問的網址
        cookies_file (str): 要使用的 cookies JSON 檔案路徑
        save_html (bool): 是否保存 HTML 檔案
    
    Returns:
        dict: 包含頁面資料的字典，失敗時返回 None
    """
    if not os.path.exists(cookies_file):
        print(f"Cookie 檔案不存在: {cookies_file}")
        return None
    
    print(f"目標 URL: {url}")
    print(f"Cookies 檔案: {cookies_file}")
    
    result = fetch_page_data(url, cookies_file, save_html)
    
    if result:
        print(f"\n成功獲取頁面資料!")
        print(f"頁面統計:")
        print(f"   - URL: {result['url']}")
        print(f"   - 標題: {result['title']}")
        print(f"   - HTML 大小: {len(result['html'])} 字元")
        print(f"   - Cookies 數量: {len(result['cookies']) if result['cookies'] else 0}")
        print(f"   - 獲取時間: {result['timestamp']}")
    else:
        print(f"獲取頁面資料失敗")
    
    return result

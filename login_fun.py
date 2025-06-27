import requests
import os
import time
import base64
import json
import random
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

config = load_config()

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        base64_string = base64.b64encode(image_file.read()).decode('utf-8')
    return base64_string

def solve_captcha(image_path):
    API_KEY = config['api']['capmonster_key']
    BASE_URL = config['api']['capmonster_url']
    
    base64_image = image_to_base64(image_path)
    
    create_task_url = f'{BASE_URL}/createTask'
    task_payload = {
        "clientKey": API_KEY,
        "task": {
            "type": "ImageToTextTask",
            "body": base64_image,
        }
    }
    response = requests.post(create_task_url, json=task_payload)
    task_result = response.json()

    if task_result.get("errorId") != 0:
        print(f"Error creating task: {task_result.get('errorDescription')}")
        return None
    
    task_id = task_result.get("taskId")
    print(f"Task created successfully. Task ID: {task_id}")
    
    result_url = f'{BASE_URL}/getTaskResult'
    result_payload = {
        "clientKey": API_KEY,
        "taskId": task_id
    }
    
    max_attempts = 10
    for _ in range(max_attempts):
        result_response = requests.post(result_url, json=result_payload)
        result_data = result_response.json()
        
        if result_data.get("status") == "ready":
            solution = result_data.get("solution", {}).get("text")
            print(f"驗證碼辨識成功: {solution}")
            return solution
        
        print("驗證碼尚未解析完成，1秒後重試...")
        time.sleep(1)
    
    return None

def setup_driver():
    """設定 Chrome WebDriver"""
    chrome_options = Options()
    
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(f"--user-data-dir=temp_chrome_profile_{int(time.time())}")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    
    
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

def download_captcha_from_selenium(driver, captcha_filename):
    """從 Selenium 中提取驗證碼圖片"""
    try:
        captcha_img = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "shCaptchaImage"))
        )
        
        script = """
        var img = arguments[0];
        var canvas = document.createElement('canvas');
        var ctx = canvas.getContext('2d');
        canvas.width = img.naturalWidth || img.width;
        canvas.height = img.naturalHeight || img.height;
        ctx.drawImage(img, 0, 0);
        return canvas.toDataURL('image/png');
        """
        
        base64_data = driver.execute_script(script, captcha_img)
        
        if base64_data and base64_data.startswith('data:image'):
            base64_data = base64_data.split(',')[1]
            image_data = base64.b64decode(base64_data)
            
            with open(captcha_filename, 'wb') as f:
                f.write(image_data)
            
            print(f"驗證碼圖片儲存成功: {captcha_filename}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"提取驗證碼時發生錯誤: {e}")
        return False

def human_type(element, text, min_delay=0.05, max_delay=0.2):
    """模擬人類打字速度"""
    element.clear()
    for char in text:
        element.send_keys(char)
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    time.sleep(random.uniform(0.3, 0.8))

def human_click(driver, element):
    """模擬人類點擊行為，包含滑鼠軌跡"""
    actions = ActionChains(driver)
    
    element_location = element.location
    element_size = element.size
    
    center_x = element_location['x'] + element_size['width'] // 2
    center_y = element_location['y'] + element_size['height'] // 2
    
    offset_x = random.randint(-10, 10)
    offset_y = random.randint(-5, 5)
    
    actions.move_to_element_with_offset(element, offset_x, offset_y)
    
    time.sleep(random.uniform(0.2, 0.5))
    
    actions.click()
    actions.perform()
    
    time.sleep(random.uniform(0.1, 0.3))

def start_login(account, password):
    driver = None
    try:
        driver = setup_driver()
        login_url = config['school']['login_url']
        
        print("正在載入登入頁面...")
        driver.get(login_url)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "LoginName"))
        )
        
        username_field = driver.find_element(By.ID, "LoginName")
        human_type(username_field, account)
        print(f"帳號已填入: {account}")
        
        password_field = driver.find_element(By.ID, "PassString")
        human_type(password_field, password)
        print("密碼已填入")
        
        captcha_image_path = f'{account}.jpg'
        if not download_captcha_from_selenium(driver, captcha_image_path):
            return {"status": "error", "message": "無法取得驗證碼"}
        
        vcode = solve_captcha(captcha_image_path)
        if not vcode:
            return {"status": "error", "message": "驗證碼解析失敗"}
        
        captcha_field = driver.find_element(By.ID, "ShCaptchaGenCode")
        human_type(captcha_field, vcode, min_delay=0.1, max_delay=0.3)
        print("驗證碼已填入")
        
        time.sleep(random.uniform(0.8, 1.5))

        login_button = driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary.loginBtnAdjust")
        human_click(driver, login_button)
        print("已點擊登入按鈕")
        
        time.sleep(3)
        
        current_url = driver.current_url
        page_source = driver.page_source
        
        try:
            os.remove(captcha_image_path)
        except:
            pass
        print(page_source)
        if "您的瀏覽器不支援框架，請更新瀏覽器版本，建議您使用 Internet Explorer 10 以上版本。" not in page_source:
            return {"status": "error", "message": "登入失敗，請再試一次"}
        
        if current_url != login_url:
            cookies = driver.get_cookies()
            cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            
            if not os.path.exists('data'):
                os.makedirs('data')
            
            cookie_file_path = f'data/{account}.json'
            with open(cookie_file_path, 'w', encoding='utf-8') as f:
                json.dump(cookie_dict, f, indent=2, ensure_ascii=False)
            print(f"Cookies 已保存到: {cookie_file_path}")
            
            return {
                "status": "success", 
                "message": "登入成功",
                "account": account,
                "cookies": cookie_dict
            }
        else:
            return {"status": "error", "message": "登入狀態不明確"}
            
    except Exception as e:
        print(f"發生未預期的錯誤: {e}")
        return {"status": "error", "message": f"未預期的錯誤: {str(e)}"}
    
    finally:
        if driver:
            driver.quit()

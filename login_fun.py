import requests
import os
import time
import base64
import json
from bs4 import BeautifulSoup

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

def start_login(account, password):
    session = requests.Session()
    base_url = config['school']['base_url']
    
    try:
        response = session.get(base_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        img_tag = soup.find('img', {'id': 'imgvcode'})
        verification_token = soup.find('input', {'name': '__RequestVerificationToken'})['value']
        print(f"Request_Verification_Token: {verification_token}")
        
        if not img_tag:
            print("找不到驗證碼圖片元素")
            return {"status": "error", "message": "無法取得驗證碼"}
        
        img_url = img_tag['src']
        if not img_url.startswith('http'):
            img_url = base_url.rstrip('/') + '/' + img_url.lstrip('/')
        
        img_response = session.get(img_url)
        img_response.raise_for_status()
        
        captcha_image_path = f'{account}.jpg'
        with open(captcha_image_path, 'wb') as f:
            f.write(img_response.content)
        print(f"驗證碼圖片儲存成功: {captcha_image_path}")
        
        vcode = solve_captcha(captcha_image_path)
        if not vcode:
            return {"status": "error", "message": "驗證碼解析失敗"}
        
        login_url = base_url.rstrip('/') + '/login.asp'
        login_data = {
            '__RequestVerificationToken': verification_token,
            'division': 'senior',
            'Loginid': account,
            'LoginPwd': password,
            'Uid': '',
            'vcode': vcode
        }
        
        login_response = session.post(login_url, data=login_data)
        login_response.raise_for_status()
        
        try:
            os.remove(captcha_image_path)
        except:
            pass
        
        response_text = login_response.text
        
        if "錯誤" in response_text:
            if "驗證碼" in response_text:
                return {"status": "error", "message": "驗證碼錯誤"}
            elif "帳號或密碼" in response_text:
                return {"status": "error", "message": "帳號或密碼錯誤"}
            else:
                return {"status": "error", "message": "未知的錯誤"}
        
        if session.cookies.items():
            cookie_name = session.cookies.items()[0][0]
            cookie_value = session.cookies.items()[0][1]
            return {
                "status": "success", 
                "message": "登入成功",
                "cookies": f"{cookie_name}={cookie_value}"
            }
        else:
            return {"status": "error", "message": "登入成功但無法獲取 cookie"}
            
    except requests.RequestException as e:
        print(f"網路請求錯誤: {e}")
        return {"status": "error", "message": f"網路請求錯誤: {str(e)}"}
    except Exception as e:
        print(f"發生未預期的錯誤: {e}")
        return {"status": "error", "message": f"未預期的錯誤: {str(e)}"}

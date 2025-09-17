from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for
import flask

import utils.login_fun as login_fun
from utils.get_fun import * 
from utils.page_fetcher import get_page_data
from utils.config import *

import time

home = Blueprint('api', __name__, url_prefix='/api')
config = load_config()

def get_page_with_session(url, account):
    if not account:
        return None
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', account):
        return None
    
    cookie_file_path = f'data/cookie/{account}.json'
    if not os.path.exists(cookie_file_path):
        return None
    
    result = get_page_data(url, cookie_file_path, save_html=False)
    return result

def load_api_key(request:flask.Request):
    api_key = request.headers.get('Authorization')
    if not api_key:
        return None
    with open('data/api/key.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    for i in data:
        if data[i]['key'] == api_key:
            return i
    return False

def load_api_token(request):
    token = request.headers.get('token')
    if not token:
        return None
    if not os.path.exists('data/api/token.json'):
        data = {}
    with open('data/api/token.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    for i in data:
        if data[i]['token'] == token:
            return i
    return False

def save_account(account):
    if not os.path.exists('data/api/token.json'):
        data = {}
    with open('data/api/token.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    new_token =  Fernet.generate_key().decode()
    data[account] = {
        "token": new_token,
        "time": int(time.time())
    }
    with open('data/api/token.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return new_token

def set_apikey_time(account):
    if not os.path.exists('data/api/key.json'):
        data = {}
    with open('data/api/key.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    if account in data:
        data[account]['time'] = int(time.time())
    with open('data/api/key.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def generate_apikey(account):
    with open('data/api/key.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    data[account] = {
        'key':Fernet.generate_key().decode(),
        'time':int(time.time())
    }
    with open('data/api/key.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return data[account]['key']

@home.route('/')
async def index():
    account = session.get("account")
    if not account or not load_cookies_from_file(account):
        return redirect("/login")

    url = f"{config['school']['base_url']}selection_student/moralculture_%20bonuspenalty.asp"

    result = get_page_with_session(url, account)
    if not result:
        return redirect("/logout")
    
    if "重新登入" in result['html']:
        return redirect("/logout")
    return render_template('api.html',api_key = request.values.get('key'))

@home.route('/generate')
async def generate():
    account = session.get("account")
    if not account or not load_cookies_from_file(account):
        return redirect("/login")

    url = f"{config['school']['base_url']}selection_student/moralculture_%20bonuspenalty.asp"
    
    result = get_page_with_session(url, account)
    if not result:
        return redirect("/logout")
    
    if "重新登入" in result['html']:
        return redirect("/logout")

    api_key = generate_apikey(account)
    return redirect(f'/api?key={api_key}')

@home.route('/login', methods=['POST'])
def login():
    """
    用戶登入 API
    接收帳號密碼，驗證格式並執行登入流程
    """
    account = request.json['account']
    password = request.json['password']
    api_account = load_api_key(request)
    if not api_account:
        return jsonify({"status": "error", "message": "未授權"}), 401
    
    if len(account) != 6:
        return jsonify({"status": "error", "message": "帳號格式錯誤，應為6位數"}), 400
    if len(password) != 10:
        return jsonify({"status": "error", "message": "密碼格式錯誤，應為10位數"}), 400
    set_apikey_time(api_account)
    data = login_fun.start_login(account, password)
    if data['status'] == 'success':
        token = save_account(account)
        data['token'] = token
        data.pop('cookies', None)
    return jsonify(data)


@home.route('/rap')
async def rap():
    """
    取得獎懲記錄 API
    返回學生的功過記錄資料
    """
    api_account = load_api_key(request)
    if not api_account:
        return jsonify({"status": "error", "message": "未授權"}), 401
    
    account = load_api_token(request)
    if not account:
        return jsonify({"status": "error", "message": "未提供帳號"}), 401

    url = f"{config['school']['base_url']}selection_student/moralculture_%20bonuspenalty.asp"
    
    result = get_page_with_session(url, account)
    if not result:
        return jsonify({"status": "error", "message": "無法取得資料"}), 500
    
    if "重新登入" in result['html']:
        return jsonify({"status": "error", "message": "登入已過期"}), 401

    data = parse_merit_demerit_records(result['html'])
    return jsonify({"status": "success", "data": data})


@home.route('/curriculum')
async def api_curriculum():
    """
    取得課表 API
    返回學生的每週課程表資料
    """
    api_account = load_api_key(request)
    if not api_account:
        return jsonify({"status": "error", "message": "未授權"}), 401
    
    account = load_api_token(request)
    if not account:
        return jsonify({"status": "error", "message": "未提供帳號"}), 401
    if not account or not load_cookies_from_file(account):
        return jsonify({"status": "error", "message": "未登入"}), 401

    url = f"{config['school']['base_url']}student/school_class_tabletime.asp?teacher_classnumber=212"
    
    result = get_page_with_session(url, account)
    if not result:
        return jsonify({"status": "error", "message": "無法取得資料"}), 500

    if "重新登入" in result['html']:
        return jsonify({"status": "error", "message": "登入已過期"}), 401
        
    data = parse_weekly_curriculum(result['html'])
    return jsonify({"status": "success", "data": data})

@home.route('/attendance')
async def api_attendance():
    """
    取得出勤記錄 API
    返回學生的出勤狀況記錄
    """
    api_account = load_api_key(request)
    if not api_account:
        return jsonify({"status": "error", "message": "未授權"}), 401
    
    account = load_api_token(request)
    if not account:
        return jsonify({"status": "error", "message": "未提供帳號"}), 401
    if not account or not load_cookies_from_file(account):
        return jsonify({"status": "error", "message": "未登入"}), 401
        
    url = f"{config['school']['base_url']}selection_student/absentation_skip_school.asp"
    
    result = get_page_with_session(url, account)
    if not result:
        return jsonify({"status": "error", "message": "無法取得資料"}), 500
    
    if "重新登入" in result['html']:
        return jsonify({"status": "error", "message": "登入已過期"}), 401

    data = parse_absence_records(result['html'], filter_types=[])
    return jsonify({"status": "success", "data": data})


@home.route('/attendance-statistics')
async def api_attendance_statistics():
    """
    取得出勤統計 API
    返回整體出勤狀況的統計資料
    """
    api_account = load_api_key(request)
    if not api_account:
        return jsonify({"status": "error", "message": "未授權"}), 401
    
    account = load_api_token(request)
    if not account:
        return jsonify({"status": "error", "message": "未提供帳號"}), 401
    if not account or not load_cookies_from_file(account):
        return jsonify({"status": "error", "message": "未登入"}), 401
        
    url = f"{config['school']['base_url']}selection_student/absentation_skip_school.asp"
    result = get_page_with_session(url, account)
    if not result:
        return jsonify({"status": "error", "message": "無法取得資料"}), 500

    if "重新登入" in result['html']:
        return jsonify({"status": "error", "message": "登入已過期"}), 401
    
    extractor = AttendanceDataExtractor(result['html'])
    statistics = extractor.get_attendance_statistics()
    
    return jsonify({"status": "success", "data": statistics})

@home.route('/score')
async def score():
    """
    取得學年成績 API
    根據指定學年返回學生的成績資料
    支援年級參數：1-4年級
    """
    api_account = load_api_key(request)
    if not api_account:
        return jsonify({"status": "error", "message": "未授權"}), 401
    
    account = load_api_token(request)
    if not account:
        return jsonify({"status": "error", "message": "未提供帳號"}), 401
    if not account or not load_cookies_from_file(account):
        return jsonify({"status": "error", "message": "未登入"}), 401
        
    year_ch = {"1": "%A4%40", "2": "%A4G","3":"%A4T","4":"%A5%7C"}
    year_num = request.values.get("year","1")
    if year_num not in year_ch:
        return jsonify({"status": "error", "message": "年級參數錯誤"}), 400
    url = f"{config['school']['base_url']}selection_student/year_accomplishment.asp?action=selection_underside_year&year_class={year_ch[year_num]}&number={year_num}"
    
    result = get_page_with_session(url, account)
    if not result:
        return jsonify({"status": "error", "message": "無法取得資料"}), 500

    if "重新登入" in result['html']:
        return jsonify({"status": "error", "message": "登入已過期"}), 401
    
    extractor = StudentGradeExtractor(result['html'])
    all_data = extractor.get_all_grade_data()
    return jsonify({"status": "success", "data": all_data})

@home.route('/all_score')
async def all_score():
    """
    取得考試成績 API
    返回考試選單與指定考試的詳細成績資料
    支援考試名稱參數篩選特定考試
    """
    api_account = load_api_key(request)
    if not api_account:
        return jsonify({"status": "error", "message": "未授權"}), 401
    
    account = load_api_token(request)
    if not account:
        return jsonify({"status": "error", "message": "未提供帳號"}), 401
    if not account or not load_cookies_from_file(account):
        return jsonify({"status": "error", "message": "未登入"}), 401
    
    url = f"{config['school']['base_url']}selection_student/student_subjects_number.asp?action=open_window_frame"
    
    result = get_page_with_session(url, account)
    if not result:
        return jsonify({"status": "error", "message": "無法取得選單資料"}), 500
    
    if "重新登入" in result['html']:
        return jsonify({"status": "error", "message": "登入已過期"}), 401
        
    menu = parse_exam_menu(result['html'])
    
    name = request.values.get("name")
    url = menu[0]['full_url']
    for i in menu:
        if i["name"] == name:
            url = i['full_url']
            break
            
    result = get_page_with_session(url, account)
    if not result:
        return jsonify({"status": "error", "message": "無法取得考試資料"}), 500
        
    data = parse_exam_scores(result['html'])
    return jsonify({
        "status": "success", 
        "data": {
            "menu": menu,
            "scores": data
        }
    })

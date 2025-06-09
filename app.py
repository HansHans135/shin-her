from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import requests
from bs4 import BeautifulSoup
import login_fun
import re
import json
from get_fun import *
import os
from page_fetcher import get_page_data
import threading
import time

app = Flask(__name__)

# 儲存登入狀態的字典
login_status = {}

def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

config = load_config()
app.config["SECRET_KEY"] = config['app']['secret_key']

def load_cookies_from_file(account):
    try:
        cookie_file_path = f'data/{account}.json'
        if os.path.exists(cookie_file_path):
            with open(cookie_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"載入 cookies 檔案時發生錯誤: {e}")
    return None

def get_headers():
    account = session.get("account")
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

@app.errorhandler(500)
async def error_500(error):
    return "發生了點錯誤，請稍後再試，或重新整理頁面。", 500

def async_login(username, password, session_id):
    """異步執行登入流程"""
    try:
        login_status[session_id] = {"status": "processing", "message": "正在處理登入..."}
        
        data = login_fun.start_login(username, password)
        
        if data["status"] == "success":
            login_status[session_id] = {
                "status": "success", 
                "message": "登入成功",
                "account": data["account"],
                "student_number": username
            }
        else:
            login_status[session_id] = {
                "status": "error", 
                "message": data["message"]
            }
    except Exception as e:
        login_status[session_id] = {
            "status": "error", 
            "message": f"登入過程中發生錯誤: {str(e)}"
        }

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form.get('password')
        privacy_agreement = request.form.get('privacy_agreement')
        
        if not password:
            return "<script>window.alert(\"請輸入密碼\");window.location.href = '/login';</script>"
        
        if not privacy_agreement:
            return "<script>window.alert(\"請先同意隱私權政策\");window.location.href = '/login';</script>"
        
        # 生成唯一的 session ID
        import uuid
        session_id = str(uuid.uuid4())
        session['login_session_id'] = session_id
        session['username'] = username
        
        # 在背景執行登入
        thread = threading.Thread(target=async_login, args=(username, password, session_id))
        thread.daemon = True
        thread.start()
        
        return redirect(url_for('waiting'))
    
    return render_template('login.html')

@app.route('/waiting')
def waiting():
    if 'login_session_id' not in session:
        return redirect(url_for('login'))
    return render_template('waiting.html')

@app.route('/api/login-status')
def api_login_status():
    session_id = session.get('login_session_id')
    if not session_id or session_id not in login_status:
        return jsonify({"status": "processing", "message": "正在處理中..."})
    
    status_data = login_status[session_id]
    
    if status_data["status"] == "success":
        # 設定 session 資料
        session["account"] = status_data["account"]
        session["student_number"] = status_data["student_number"]
        
        # 清理登入狀態
        del login_status[session_id]
        del session['login_session_id']
        del session['username']
    
    return jsonify(status_data)

def get_page_with_session(url):
    account = session.get("account")
    if not account:
        return None
    
    cookie_file_path = f'data/{account}.json'
    if not os.path.exists(cookie_file_path):
        return None
    
    result = get_page_data(url, cookie_file_path, save_html=False)
    return result

@app.route('/')
async def index():
    account = session.get("account")
    if not account or not load_cookies_from_file(account):
        return redirect("/login")

    url = f"{config['school']['base_url']}selection_student/moralculture_%20bonuspenalty.asp"
    
    result = get_page_with_session(url)
    if not result:
        return redirect("/logout")
    
    if "重新登入" in result['html']:
        return redirect("/logout")

    data = parse_merit_demerit_records(result['html'])
    return render_template('index.html', data=data)

@app.route('/privacy')
async def privacy():
    return render_template('privacy.html')

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route('/api/curriculum')
async def api_curriculum():
    account = session.get("account")
    if not account or not load_cookies_from_file(account):
        return redirect("/login")

    url = f"{config['school']['base_url']}student/school_class_tabletime.asp?teacher_classnumber=212"
    
    result = get_page_with_session(url)
    if not result:
        return redirect("/logout")

    if "重新登入" in result['html']:
        return redirect("/logout")
        
    d1 = parse_weekly_curriculum(result['html'])
    return d1

@app.route('/api/attendance')
async def api_attendance():
    account = session.get("account")
    if not account or not load_cookies_from_file(account):
        return redirect("/login")
        
    url = f"{config['school']['base_url']}selection_student/absentation_skip_school.asp"
    
    result = get_page_with_session(url)
    if not result:
        return redirect("/logout")
    
    if "重新登入" in result['html']:
        return redirect("/logout")
        
    d2 = parse_absence_records(result['html'], filter_types=[])
    return d2

@app.route('/curriculum')
async def curriculum():
    account = session.get("account")
    if not account or not load_cookies_from_file(account):
        return redirect("/login")
    return render_template("curriculum.html")

@app.route('/attend')
async def attend():
    account = session.get("account")
    if not account or not load_cookies_from_file(account):
        return redirect("/login")
        
    absence_url = f"{config['school']['base_url']}selection_student/absentation_skip_school.asp"
    absence_result = get_page_with_session(absence_url)
    if not absence_result:
        return redirect("/logout")

    curriculum_url = f"{config['school']['base_url']}student/school_class_tabletime.asp?teacher_classnumber=212"
    curriculum_result = get_page_with_session(curriculum_url)
    if not curriculum_result:
        return redirect("/logout")

    if "重新登入" in absence_result['html'] or "重新登入" in curriculum_result['html']:
        return redirect("/logout")
    
    d1 = parse_weekly_curriculum(curriculum_result['html'])
    d2 = parse_absence_records(absence_result['html'])
    y = extract_semester_info(curriculum_result['html'])
    
    d3 = calculate_subject_absences(d1, d2, "上" if y["semester"]=="1" else "下")
    for i in d3.copy():
        d3[i]["all"] = d1[i]['count']*config['school']['weeks_per_semester']
        d3[i]["percent"] = int((d3[i]['總計']/d3[i]["all"])*100)

    # 獲取出席統計
    extractor = AttendanceDataExtractor(absence_result['html'])
    statistics = extractor.get_attendance_statistics()
    
    return render_template("attend.html", attendance_data=statistics, data=d3)

@app.route('/score')
async def score():
    account = session.get("account")
    if not account or not load_cookies_from_file(account):
        return redirect("/login")
        
    year_ch = {"1": "%A4%40", "2": "%A4G","3":"%A4T","4":"%A5%7C"}
    year_num = request.values.get("year") or "1"
    url = f"{config['school']['base_url']}selection_student/year_accomplishment.asp?action=selection_underside_year&year_class={year_ch[year_num]}&number={year_num}"
    
    result = get_page_with_session(url)
    if not result:
        return redirect("/logout")

    if "重新登入" in result['html']:
        return redirect("/logout")
    
    extractor = StudentGradeExtractor(result['html'])
    all_data = extractor.get_all_grade_data()
    return render_template("score.html", data=all_data)

@app.route('/all_score')
async def all_score():
    account = session.get("account")
    if not account or not load_cookies_from_file(account):
        return redirect("/login")
    
    url = f"{config['school']['base_url']}selection_student/student_subjects_number.asp?action=open_window_frame"
    
    result = get_page_with_session(url)
    if not result:
        return redirect("/logout")
    
    if "重新登入" in result['html']:
        return redirect("/logout")
        
    menu = parse_exam_menu(result['html'])
    
    name = request.values.get("name")
    url = menu[0]['full_url']
    for i in menu:
        if i["name"] == name:
            url = i['full_url']
            break
            
    result = get_page_with_session(url)
    if not result:
        return redirect("/logout")
        
    data = parse_exam_scores(result['html'])
    return render_template("all_score.html", menu=menu, data=data)

app.run(host=config['app']['host'], port=config['app']['port'], debug=config['app']['debug'])

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import requests
from bs4 import BeautifulSoup
import login_fun
import re
import json
from get_fun import *

app = Flask(__name__)

def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

config = load_config()
app.config["SECRET_KEY"] = config['app']['secret_key']

def get_headers():
    if not session.get("cookies"):
        return None
    
    headers = {
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "zh-TW,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "cache-control": "no-cache",
        "cookie": "; ".join([f"{k}={v}" for k, v in session.get("cookies", {}).items()]),
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0"
    }
    return headers

@app.errorhandler(500)
async def error_500(error):
    return "發生了點錯誤，請稍後再試，或重新整理頁面。", 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form.get('password')
        if not password:
            return "<script>window.alert(\"請輸入密碼\");window.location.href = '/login';</script>"
        
        data = login_fun.start_login(username, password)
        if data["status"] == "success":
            session["student_number"] = username
            session["cookies"] = data["cookies"]  # 存储所有cookie到session
            return redirect("/")
        else:
            return f"<script>window.alert(\"{data['message']}\");window.location.href = '/login';</script>"
    return render_template('login.html')

@app.route('/')
async def index():
    access_token = session.get("student_number")
    if not access_token or not session.get("cookies"):
        return redirect("/login")

    url = f"{config['school']['base_url']}selection_student/moralculture_%20bonuspenalty.asp"
    headers = get_headers()
    response = requests.get(url, headers=headers)
    
    if "重新登入" in response.text:
        return redirect("/logout")

    data = parse_merit_demerit_records(response.text)
    return render_template('index.html', data=data)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route('/api/curriculum')
async def api_curriculum():
    if not session.get("student_number") or not session.get("cookies"):
        return redirect("/login")

    url = f"{config['school']['base_url']}student/school_class_tabletime.asp?teacher_classnumber=212"
    headers = get_headers()
    response = requests.get(url, headers=headers)

    if "重新登入" in response.text:
        return redirect("/logout")
    d1=parse_weekly_curriculum(response.text)
    return d1

@app.route('/api/attendance')
async def api_attendance():
    if not session.get("student_number") or not session.get("cookies"):
        return redirect("/login")
        
    url = f"{config['school']['base_url']}selection_student/absentation_skip_school.asp"
    headers = get_headers()
    response = requests.get(url, headers=headers)
    
    if "重新登入" in response.text:
        return redirect("/logout")
    d2=parse_absence_records(response.text,filter_types=[])
    return d2

@app.route('/curriculum')
async def curriculum():
    if not session.get("student_number") or not session.get("cookies"):
        return redirect("/login")
    return render_template("curriculum.html")

@app.route('/attend')
async def attend():
    if not session.get("student_number") or not session.get("cookies"):
        return redirect("/login")
        
    url = f"{config['school']['base_url']}selection_student/absentation_skip_school.asp"
    headers = get_headers()
    response = requests.get(url, headers=headers)

    url = f"{config['school']['base_url']}student/school_class_tabletime.asp?teacher_classnumber=212"
    response1 = requests.get(url, headers=headers)

    if "重新登入" in response.text:
        return redirect("/logout")
    
    d1=parse_weekly_curriculum(response1.text)
    d2=parse_absence_records(response.text)
    y=extract_semester_info(response1.text)
    d3=calculate_subject_absences(d1,d2,"上" if y["semester"]=="1" else "下")
    for i in d3.copy():
        d3[i]["all"]=d1[i]['count']*config['school']['weeks_per_semester'] #總結數
        d3[i]["percent"]=int((d3[i]['總計']/d3[i]["all"])*100)

    extractor = AttendanceDataExtractor(response.text)
    statistics = extractor.get_attendance_statistics()
    return render_template("attend.html", attendance_data=statistics,data=d3)

@app.route('/score')
async def score():
    if not session.get("student_number") or not session.get("cookies"):
        return redirect("/login")
        
    year_ch = {"1": "%A4%40", "2": "%A4G","3":"%A4T","4":"%A5%7C"}
    year_num=request.values.get("year") or "1"
    url = f"{config['school']['base_url']}selection_student/year_accomplishment.asp?action=selection_underside_year&year_class={year_ch[year_num]}&number={year_num}"
    headers = get_headers()
    response = requests.get(url, headers=headers)

    if "重新登入" in response.text:
        return redirect("/logout")
    
    extractor = StudentGradeExtractor(response.text)
    all_data = extractor.get_all_grade_data()
    return render_template("score.html", data=all_data)

@app.route('/all_score')
async def all_score():
    if not session.get("student_number") or not session.get("cookies"):
        return redirect("/login")
    
    url= f"{config['school']['base_url']}selection_student/student_subjects_number.asp?action=open_window_frame"
    headers = get_headers()
    response = requests.get(url, headers=headers)
    
    if "重新登入" in response.text:
        return redirect("/logout")
    menu= parse_exam_menu(response.text)
    
    name=request.values.get("name")
    url= menu[0]['full_url']
    for i in menu:
        if i["name"]==name:
            url = i['full_url']
            break
    response = requests.get(url, headers=headers)
    data= parse_exam_scores(response.text)
    return render_template("all_score.html",menu=menu,data=data)

app.run(host=config['app']['host'], port=config['app']['port'], debug=config['app']['debug'])

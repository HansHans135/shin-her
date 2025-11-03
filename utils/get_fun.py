from bs4 import BeautifulSoup
import re
import json
from collections import defaultdict
from urllib.parse import unquote

def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

config = load_config()

def parse_merit_demerit_records(html_text):
    soup = BeautifulSoup(html_text, 'html.parser')
    table = soup.find('table', class_='rpDetail')
    merits = []
    demerits = []
    for row in table.find_all('tr', class_='dataRow'):  # type: ignore
        cells = row.find_all('td')
        if len(cells) == 7:
            record_type = cells[0].text.strip()
            date_occurred = cells[1].text.strip()
            date_approved = cells[2].text.strip()
            reason = cells[3].text.strip()
            action = cells[4].text.strip()
            date_revoked = cells[5].text.strip() or None
            year = cells[6].text.strip()
            record = {
                "date_occurred": date_occurred,
                "date_approved": date_approved,
                "reason": reason,
                "action": action,
                "date_revoked": date_revoked,
                "year": year
            }
            if record_type == "獎勵":
                merits.append(record)
            elif record_type == "懲罰":
                demerits.append(record)
    return [merits, demerits]

class AttendanceDataExtractor:
    def __init__(self, html_content):
        self.soup = BeautifulSoup(html_content, 'html.parser')

    def extract_row_data(self, row):
        return [cell.text.strip() for cell in row.find_all('td')]

    def extract_table_data(self, table):
        rows = table.find_all('tr')
        headers = []
        data = {}
        current_semester = None

        for row in rows:
            cells = self.extract_row_data(row)
            if len(cells) == 1 and '學期合計' in cells[0]:
                current_semester = cells[0].replace('合計', '').strip()
                data[current_semester] = {}
            elif len(cells) > 1 and current_semester:
                if not headers:
                    headers = cells
                else:
                    for header, value in zip(headers, cells):
                        data[current_semester][header] = value if value and value != '&nbsp;' else '0'        
        data["全部"]={
            "曠課":0+int(data["上學期"]["曠課"])+int(data["下學期"]["曠課"]),
            "事假":0+int(data["上學期"]["事假"])+int(data["下學期"]["事假"])+int(data["上學期"]["事假1"])+int(data["下學期"]["事假1"]),
            "病假":0+int(data["上學期"]["病假"])+int(data["下學期"]["病假"])+int(data["上學期"]["病假1"])+int(data["下學期"]["病假1"])+int(data["上學期"]["病假2"])+int(data["下學期"]["病假2"]),
            "公假":0+int(data["上學期"]["公假"])+int(data["下學期"]["公假"]),
            
        }
        return data

    def get_attendance_statistics(self):
        attendance_table = self.soup.find(
            'table', class_='collapse', style=lambda value: value and 'width: 100%' in value)  # type: ignore

        if not attendance_table:
            return {"error": "無法找到缺曠統計資料表格。請檢查HTML結構是否有變化。"}

        attendance_data = self.extract_table_data(attendance_table)

        result = {}
        for semester, data in attendance_data.items():
            result[f"{semester}合計"] = data

        date_info = self.soup.find('td', string=re.compile(r'以上資料為本學年至.*之累計'))
        if date_info:
            result["統計日期"] = date_info.text.strip()

        return result

    def get_student_info(self):
        info_div = self.soup.find('div', style='vertical-align: bottom;')
        if info_div:
            return info_div.text.strip()
        return "無法找到學生資訊"


class StudentGradeExtractor:
    def __init__(self, html_content):
        self.soup = BeautifulSoup(html_content, 'html.parser')

    def extract_student_info(self):
        info_div = self.soup.find('div', style='vertical-align: bottom;')
        if info_div:
            return info_div.text.strip()
        return "無法找到學生資訊"

    def extract_subjects(self):
        subjects = []
        table = self.soup.find('table', class_='border-collapse')
        if table:
            rows = table.find_all('tr')[2:]   # type: ignore
            for row in rows:
                cells = row.find_all('td')
                if len(cells) == 8:
                    subject = {
                        '科目': cells[0].text.strip(),
                        '上學期': {
                            '屬性': cells[1].text.strip(),
                            '學分': cells[2].text.strip(),
                            '成績': cells[3].text.strip()
                        },
                        '下學期': {
                            '屬性': cells[4].text.strip(),
                            '學分': cells[5].text.strip(),
                            '成績': cells[6].text.strip()
                        },
                        '學年成績': cells[7].text.strip()
                    }
                    subjects.append(subject)
                elif '重(補)修科目' in row.text:
                    break
        return subjects

    def extract_total_scores(self):
        total_scores = {}
        table = self.soup.find(
            'table', class_='collapse brk01 padding3 spacing0')
        if table:
            rows = table.find_all('tr')[1:]  # type: ignore
            for row in rows:
                cells = row.find_all('td')
                if len(cells) == 4:
                    category = cells[0].text.strip()
                    total_scores[category] = {
                        '上學期': cells[1].text.strip(),
                        '下學期': cells[2].text.strip(),
                        '學年': cells[3].text.strip()
                    }
        return total_scores

    def extract_daily_performance(self):
        daily_performance = {'上學期': {}, '下學期': {}}
        table = self.soup.find(
            'table', class_='brk01 collapse padding3 spacing0')
        if table:
            current_semester = None
            for row in table.find_all('tr'):  # type: ignore
                if '上學期' in row.text:
                    current_semester = '上學期'
                elif '下學期' in row.text:
                    current_semester = '下學期'
                elif current_semester and len(row.find_all('td')) == 6:
                    cells = row.find_all('td')
                    daily_life_content = str(cells[0])
                    daily_life_content = daily_life_content.replace('<td>', '').replace('</td>', '').strip()
                    
                    daily_performance[current_semester] = {
                        '日常生活表現': {'評量': daily_life_content, '描述': cells[1].text.strip()},
                        '服務學習': cells[2].text.strip(),
                        '校內外特殊表現': cells[3].text.strip(),
                        '具體建議及評語': cells[4].text.strip(),
                        '其他': cells[5].text.strip()
                    }
        return daily_performance

    def get_all_grade_data(self):
        return {
            '學生資訊': self.extract_student_info(),
            '科目成績': self.extract_subjects(),
            '總成績': self.extract_total_scores(),
            '日常表現': self.extract_daily_performance()
        }
    
def parse_weekly_curriculum(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    table = soup.find("table", class_="TimeTable")
    if not table:
        return {}
    
    rows = table.find_all("tr")
    header_tds = rows[0].find_all("td")
    weekdays = [td.get_text(strip=True) for td in header_tds[3:]]
    
    result = {}
    
    for tr in rows[1:]:
        tds = tr.find_all("td")
        if not tds:
            continue
        if tds[0].has_attr("rowspan"):
            period = tds[1].get_text(strip=True)
            course_cells = tds[3:]
        else:
            period = tds[0].get_text(strip=True)
            course_cells = tds[2:]
        if not period:
            continue
        
        m = re.search(r'第(.+)節', period)
        if m:
            period = m.group(1)
    
        for idx, cell in enumerate(course_cells):
            cell_text = cell.get_text(separator="\n", strip=True)
            if not cell_text:
                continue
            subject = cell_text.split("\n")[0]
            weekday_mapping = {0: "一", 1: "二", 2: "三", 3: "四", 4: "五", 5: "六", 6: "日"}
            weekday = f"{weekday_mapping.get(idx % 7, str(idx+1))}"
            if subject not in result:
                result[subject] = {"count": 0, "schedule": []}
            result[subject]["count"] += 1
            result[subject]["schedule"].append({"weekday": weekday, "period": period})
    
    return result

def parse_absence_records(html_content, filter_types=["曠", "事"]):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    table = soup.find('table', class_="padding2 spacing0")
    if table is None:
        return []

    header_tr = table.find('tr', class_="td_03")
    headers = [th.get_text(strip=True) for th in header_tr.find_all('td')]
    
    results = []
    rows = table.find_all('tr')[1:]
    for row in rows:
        cells = [td.get_text(strip=True) for td in row.find_all('td')]
        if len(cells) < 3:
            continue
        academic_term = cells[0]
        date = cells[1]
        weekday = cells[2]
        for i, cell in enumerate(cells[3:], start=3):
            if cell in ["曠", "事"] or len(filter_types)==0:
                period = headers[i] if i < len(headers) else f"col{i}"
                # 過濾出數字期間
                if period.isdigit():
                    if cell!="":
                        results.append({
                            "學年": academic_term[0],
                            "日期": date,
                            "星期": weekday,
                            "節次": period,
                            "狀態": cell
                        })
    return results

    
def calculate_subject_absences(curriculum_data, absence_data, semester):
    course_mapping = {}
    for course_name, course_info in curriculum_data.items():
        for schedule in course_info["schedule"]:
            weekday = schedule["weekday"]
            period = schedule["period"]
            course_mapping[(weekday, period)] = course_name

    absence_count = defaultdict(lambda: {"曠課": 0, "事假": 0})

    number_map = {
        "1": "一",
        "2": "二",
        "3": "三",
        "4": "四",
        "5": "五",
        "6": "六",
        "7": "七"
    }

    for record in absence_data:
        if record["學年"] != semester:
            continue
        weekday = record["星期"]
        period = record["節次"]
        status = record["狀態"]
        
        chinese_period = number_map[period]
        
        course = course_mapping.get((weekday, chinese_period))
        
        if course:
            if status == "曠":
                absence_count[course]["曠課"] += 1
            elif status == "事":
                absence_count[course]["事假"] += 1

    result = {}
    for course, counts in absence_count.items():
        result[course] = {
            "曠課": counts["曠課"],
            "事假": counts["事假"],
            "總計": counts["曠課"] + counts["事假"]
        }

    return result

def extract_semester_info(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    semester_td = soup.find('td', class_='center', style='height: 400px;')
    
    if semester_td:
        semester_text = semester_td.get_text(strip=True)
        
        year_match = re.search(r'(\d+)學年度', semester_text)
        semester_match = re.search(r'第(\d+)學期', semester_text)
        
        if year_match and semester_match:
            school_year = year_match.group(1)
            semester = semester_match.group(1)
            
            return {
                'school_year': school_year,
                'semester': semester
            }
    
    return None


def parse_exam_menu(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    select_element = soup.find('select', {'id': 'ddlExamList'})
    
    if not select_element:
        return []
    
    exam_list = []
    
    for option in select_element.find_all('option'):
        value = option.get('value', '')
        text = option.get_text(strip=True)
        
        if value and text:
            value = value.replace('&amp;', '&')
            
            exam_info = {
                'name': text,
                'url': value,
                'full_url': f'{config["school"]["base_url"]}selection_student/{value}'
            }
            
            if 'student_subjects_number.asp' in value and 'action=' in value:
                exam_info.update(parse_exam_url_params(value))
            
            exam_list.append(exam_info)
    
    return exam_list

def parse_exam_url_params(url):
    params = {}
    
    param_patterns = {
        'thisyear': r'thisyear=(\d+)',
        'thisterm': r'thisterm=(\d+)',
        'number': r'number=(\d+)',
        'exam_name': r'exam_name=([^&]+)'
    }
    
    for param_name, pattern in param_patterns.items():
        match = re.search(pattern, url)
        if match:
            value = match.group(1)
            if param_name == 'exam_name':
                try:
                    value = unquote(value, encoding='big5')
                except:
                    pass
            params[param_name] = value
    
    return params

def parse_exam_scores(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    info_div = soup.find('div', class_='center mobile-text-center pt-2')
    info_text = info_div.get_text() if info_div else ""
    
    student_id = re.search(r'學號：(\d+)', info_text)
    student_name = re.search(r'姓名：([^　\s]+)', info_text)
    class_name = re.search(r'班級：([^　\s]+)', info_text)
    
    exam_info_span = soup.find('span', class_='bluetext')
    exam_info = exam_info_span.get_text() if exam_info_span else ""
    
    subjects = []
    score_table = soup.find('table', id='Table1')
    if score_table:
        rows = score_table.find_all('tr')[1:]
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 3 and cells[0].get_text().strip():
                subject_name = cells[0].get_text().strip()
                
                if not subject_name or subject_name == "":
                    continue
                    
                score_cell = cells[1]
                score_span = score_cell.find('span')
                if score_span:
                    personal_score = score_span.get_text().strip()
                else:
                    personal_score = score_cell.get_text().strip()
                
                avg_cell = cells[2]
                avg_span = avg_cell.find('span')
                if avg_span:
                    class_average = avg_span.get_text().strip()
                else:
                    class_average = avg_cell.get_text().strip()
                
                subjects.append({
                    "subject": subject_name,
                    "personal_score": personal_score,
                    "class_average": class_average
                })
    
    summary_table = soup.find('table', class_='scoreTable-inline')
    total_score = ""
    average_score = ""
    class_rank = ""
    department_rank = ""
    
    if summary_table:
        cells = summary_table.find_all('td')
        for i, cell in enumerate(cells):
            text = cell.get_text().strip()
            if text == "總分：" and i + 1 < len(cells):
                total_score = cells[i + 1].get_text().strip()
            elif text == "平均：" and i + 1 < len(cells):
                avg_span = cells[i + 1].find('span')
                average_score = avg_span.get_text().strip() if avg_span else cells[i + 1].get_text().strip()
            elif text == "排名：" and i + 1 < len(cells):
                class_rank = cells[i + 1].get_text().strip()
            elif text == "科別排名：" and i + 1 < len(cells):
                department_rank = cells[i + 1].get_text().strip()
    
    result = {
        "student_info": {
            "student_id": student_id.group(1) if student_id else "",
            "name": student_name.group(1) if student_name else "",
            "class": class_name.group(1) if class_name else ""
        },
        "exam_info": exam_info,
        "subjects": subjects,
        "summary": {
            "total_score": total_score,
            "average_score": average_score,
            "class_rank": class_rank,
            "department_rank": department_rank
        }
    }
    
    return result